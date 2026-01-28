"""
Market Data API Views - REST API endpoints.

Provides ViewSets for:
- Exchange CRUD
- TradingPair CRUD
- OHLCV data retrieval
- CorrelationMatrix retrieval
- Data fetch triggers

URL namespace: api:v1:market_data
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from apps.core.views_api import BaseModelViewSet
from .models import Exchange, TradingPair, OHLCV, CorrelationMatrix
from .serializers import (
    ExchangeSerializer, ExchangeListSerializer,
    TradingPairSerializer, TradingPairListSerializer,
    OHLCVSerializer, OHLCVListSerializer, OHLCVCreateSerializer,
    CorrelationMatrixSerializer, FetchDataSerializer
)


class ExchangeViewSet(BaseModelViewSet):
    """
    ViewSet for Exchange CRUD operations.

    Provides:
    - list: GET /api/v1/market-data/exchanges/
    - retrieve: GET /api/v1/market-data/exchanges/{uuid}/
    - create: POST /api/v1/market-data/exchanges/
    - update: PUT /api/v1/market-data/exchanges/{uuid}/
    - partial_update: PATCH /api/v1/market-data/exchanges/{uuid}/
    - destroy: DELETE /api/v1/market-data/exchanges/{uuid}/
    """
    queryset = Exchange.objects.all()
    serializer_class = ExchangeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['api_type', 'is_enabled']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return ExchangeListSerializer
        return ExchangeSerializer


class TradingPairViewSet(BaseModelViewSet):
    """
    ViewSet for TradingPair CRUD operations.

    Provides:
    - list: GET /api/v1/market-data/trading-pairs/
    - retrieve: GET /api/v1/market-data/trading-pairs/{uuid}/
    - create: POST /api/v1/market-data/trading-pairs/
    - update: PUT /api/v1/market-data/trading-pairs/{uuid}/
    - partial_update: PATCH /api/v1/market-data/trading-pairs/{uuid}/
    - destroy: DELETE /api/v1/market-data/trading-pairs/{uuid}/

    Custom actions:
    - forex: GET /api/v1/market-data/trading-pairs/forex/
    - crypto: GET /api/v1/market-data/trading-pairs/crypto/
    """
    queryset = TradingPair.objects.select_related('exchange')
    serializer_class = TradingPairSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['exchange', 'is_forex', 'base_currency', 'quote_currency']
    search_fields = ['symbol', 'base_currency', 'quote_currency']
    ordering_fields = ['symbol', 'created_at']
    ordering = ['symbol']

    def get_serializer_class(self):
        if self.action == 'list':
            return TradingPairListSerializer
        return TradingPairSerializer

    @action(detail=False, methods=['get'])
    def forex(self, request):
        """Get all forex pairs."""
        pairs = self.get_queryset().filter(is_forex=True)
        serializer = TradingPairListSerializer(pairs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def crypto(self, request):
        """Get all crypto pairs."""
        pairs = self.get_queryset().filter(is_forex=False)
        serializer = TradingPairListSerializer(pairs, many=True)
        return Response(serializer.data)


class OHLCVViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for OHLCV data retrieval (read-only).

    Provides:
    - list: GET /api/v1/market-data/ohlcv/
    - retrieve: GET /api/v1/market-data/ohlcv/{uuid}/

    Custom actions:
    - chart_data: GET /api/v1/market-data/ohlcv/chart-data/
    - latest: GET /api/v1/market-data/ohlcv/latest/
    """
    queryset = OHLCV.objects.select_related('trading_pair')
    serializer_class = OHLCVSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['trading_pair', 'timeframe']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    def get_serializer_class(self):
        if self.action == 'chart_data':
            return OHLCVListSerializer
        return OHLCVSerializer

    @action(detail=False, methods=['get'])
    def chart_data(self, request):
        """
        Get OHLCV data formatted for charts.

        Query params:
        - trading_pair: UUID of the trading pair
        - timeframe: '15m', '1h', '4h', '1d'
        - limit: number of candles (default 100)
        """
        trading_pair_id = request.query_params.get('trading_pair')
        timeframe = request.query_params.get('timeframe', '1h')
        limit = int(request.query_params.get('limit', 100))

        if not trading_pair_id:
            return Response(
                {'error': 'trading_pair is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(
            trading_pair_id=trading_pair_id,
            timeframe=timeframe
        ).order_by('-timestamp')[:limit]

        # Reverse to get chronological order
        data = list(queryset)
        data.reverse()

        serializer = OHLCVListSerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """
        Get the latest OHLCV record for a trading pair.

        Query params:
        - trading_pair: UUID of the trading pair
        - timeframe: '15m', '1h', '4h', '1d'
        """
        trading_pair_id = request.query_params.get('trading_pair')
        timeframe = request.query_params.get('timeframe', '1h')

        if not trading_pair_id:
            return Response(
                {'error': 'trading_pair is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            latest = self.get_queryset().filter(
                trading_pair_id=trading_pair_id,
                timeframe=timeframe
            ).latest('timestamp')
            serializer = OHLCVSerializer(latest)
            return Response(serializer.data)
        except OHLCV.DoesNotExist:
            return Response(
                {'error': 'No data found'},
                status=status.HTTP_404_NOT_FOUND
            )


class CorrelationMatrixViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for CorrelationMatrix retrieval (read-only).

    Provides:
    - list: GET /api/v1/market-data/correlations/
    - retrieve: GET /api/v1/market-data/correlations/{uuid}/
    """
    queryset = CorrelationMatrix.objects.select_related('primary_pair', 'secondary_pair')
    serializer_class = CorrelationMatrixSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['primary_pair', 'secondary_pair', 'timeframe']
    ordering_fields = ['correlation_value', 'calculation_date']
    ordering = ['-calculation_date']


class FetchDataAPIView(APIView):
    """
    API endpoint to trigger data fetching.

    POST /api/v1/market-data/fetch/
    """

    def post(self, request):
        """Trigger data fetch for a trading pair."""
        serializer = FetchDataSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # In production, this would trigger a Celery task
        # For now, return a placeholder response
        return Response({
            'status': 'queued',
            'message': 'Data fetch task has been queued',
            'trading_pair_id': str(serializer.validated_data['trading_pair_id']),
            'timeframe': serializer.validated_data['timeframe'],
        }, status=status.HTTP_202_ACCEPTED)
