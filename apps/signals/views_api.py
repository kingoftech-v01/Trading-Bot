"""
API Views for the signals app.

Following URL_AND_VIEW_CONVENTIONS.md:
- Namespace: api:v1:signals
- JSON responses only
- Uses DRF ViewSets and APIView
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.utils import timezone

from .models import Vote, SignalSession, Signal, ConfluenceScore
from .serializers import (
    VoteSerializer,
    VoteListSerializer,
    SignalSessionSerializer,
    SignalSessionListSerializer,
    SignalSerializer,
    SignalListSerializer,
    ConfluenceScoreSerializer,
    GenerateSignalSerializer,
    SignalGenerationResultSerializer,
)
from .services import SignalGenerator, VotingSystem
from apps.market_data.models import TradingPair, OHLCV


class VoteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Vote read operations.

    list: GET /api/v1/signals/votes/
    retrieve: GET /api/v1/signals/votes/{id}/
    """

    queryset = Vote.objects.select_related(
        'combination', 'trading_pair', 'signal_session'
    ).order_by('-created_at')
    serializer_class = VoteSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['combination', 'trading_pair', 'signal', 'signal_session']
    ordering_fields = ['created_at', 'confidence']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return VoteListSerializer
        return VoteSerializer


class SignalSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for SignalSession read operations.

    list: GET /api/v1/signals/sessions/
    retrieve: GET /api/v1/signals/sessions/{id}/
    """

    queryset = SignalSession.objects.select_related(
        'trading_pair'
    ).prefetch_related('votes').order_by('-evaluated_at')
    serializer_class = SignalSessionSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['trading_pair', 'final_signal', 'timeframe']
    ordering_fields = ['evaluated_at', 'confluence_score', 'buy_votes', 'sell_votes']
    ordering = ['-evaluated_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return SignalSessionListSerializer
        return SignalSessionSerializer

    @action(detail=False, methods=['get'])
    def actionable(self, request):
        """
        Get only actionable sessions (buy/sell signals).

        GET /api/v1/signals/sessions/actionable/
        """
        sessions = self.get_queryset().filter(
            final_signal__in=['buy', 'sell']
        )[:50]
        serializer = SignalSessionListSerializer(sessions, many=True)
        return Response(serializer.data)


class SignalViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Signal CRUD operations.

    list: GET /api/v1/signals/signals/
    retrieve: GET /api/v1/signals/signals/{id}/
    """

    queryset = Signal.objects.select_related(
        'trading_pair', 'session'
    ).order_by('-created_at')
    serializer_class = SignalSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['trading_pair', 'signal', 'status', 'timeframe']
    ordering_fields = ['created_at', 'confluence_score', 'vote_count']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return SignalListSerializer
        return SignalSerializer

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get active (pending, not expired) signals.

        GET /api/v1/signals/signals/active/
        """
        signals = self.get_queryset().filter(
            status='pending',
            expires_at__gt=timezone.now(),
        )
        serializer = SignalListSerializer(signals, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        Mark a signal as executed.

        POST /api/v1/signals/signals/{id}/execute/
        """
        signal = self.get_object()
        if signal.status != 'pending':
            return Response(
                {'error': f'Cannot execute signal with status: {signal.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        signal.mark_executed()
        serializer = SignalSerializer(signal)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a signal.

        POST /api/v1/signals/signals/{id}/cancel/
        """
        signal = self.get_object()
        if signal.status != 'pending':
            return Response(
                {'error': f'Cannot cancel signal with status: {signal.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        signal.mark_cancelled()
        serializer = SignalSerializer(signal)
        return Response(serializer.data)


class ConfluenceScoreViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for ConfluenceScore read operations.

    list: GET /api/v1/signals/confluence/
    retrieve: GET /api/v1/signals/confluence/{id}/
    """

    queryset = ConfluenceScore.objects.select_related(
        'trading_pair', 'session'
    ).order_by('-created_at')
    serializer_class = ConfluenceScoreSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['trading_pair', 'timeframe']
    ordering_fields = ['created_at', 'total_score']
    ordering = ['-created_at']


class GenerateSignalAPIView(APIView):
    """
    Generate a trading signal for a pair.

    POST /api/v1/signals/generate/
    """

    def post(self, request):
        serializer = GenerateSignalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        trading_pair_id = serializer.validated_data['trading_pair_id']
        timeframe = serializer.validated_data['timeframe']
        min_confluence = serializer.validated_data.get('min_confluence', 50.0)
        min_confidence = serializer.validated_data.get('min_confidence', 60.0)

        # Get trading pair
        try:
            trading_pair = TradingPair.objects.get(id=trading_pair_id)
        except TradingPair.DoesNotExist:
            return Response(
                {'error': 'Trading pair not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get OHLCV data
        ohlcv_qs = OHLCV.objects.filter(
            trading_pair=trading_pair,
            timeframe=timeframe
        ).order_by('-timestamp')[:200]

        if not ohlcv_qs.exists():
            return Response(
                {'error': 'No OHLCV data available'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Convert to list of dicts
        ohlcv_data = list(ohlcv_qs.values(
            'timestamp', 'open', 'high', 'low', 'close', 'volume'
        ))
        ohlcv_data.reverse()  # Oldest first

        # Generate signal
        generator = SignalGenerator(
            min_confluence=min_confluence,
            min_confidence=min_confidence,
        )
        result = generator.generate_signal(
            trading_pair=trading_pair,
            ohlcv_data=ohlcv_data,
            timeframe=timeframe,
        )

        if result.success:
            return Response(result.data)
        else:
            return Response(
                {'error': result.error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VotingStatusAPIView(APIView):
    """
    Get voting status for a pair without generating a signal.

    POST /api/v1/signals/voting-status/
    """

    def post(self, request):
        trading_pair_id = request.data.get('trading_pair_id')
        timeframe = request.data.get('timeframe', '1h')

        if not trading_pair_id:
            return Response(
                {'error': 'trading_pair_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get trading pair
        try:
            trading_pair = TradingPair.objects.get(id=trading_pair_id)
        except TradingPair.DoesNotExist:
            return Response(
                {'error': 'Trading pair not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get OHLCV data
        ohlcv_qs = OHLCV.objects.filter(
            trading_pair=trading_pair,
            timeframe=timeframe
        ).order_by('-timestamp')[:200]

        if not ohlcv_qs.exists():
            return Response(
                {'error': 'No OHLCV data available'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ohlcv_data = list(ohlcv_qs.values(
            'timestamp', 'open', 'high', 'low', 'close', 'volume'
        ))
        ohlcv_data.reverse()

        # Get voting status
        voting_system = VotingSystem()
        voting_result = voting_system.collect_votes(ohlcv_data)
        summary = voting_system.get_voting_summary(voting_result)

        return Response({
            'trading_pair': trading_pair.symbol,
            'timeframe': timeframe,
            'voting_summary': summary,
        })
