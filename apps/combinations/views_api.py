"""
API Views for the combinations app.

Following URL_AND_VIEW_CONVENTIONS.md:
- Namespace: api:v1:combinations
- JSON responses only
- Uses DRF ViewSets and APIView
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Combination, CombinationResult
from .serializers import (
    CombinationSerializer,
    CombinationListSerializer,
    CombinationResultSerializer,
    CombinationResultListSerializer,
    EvaluateCombinationSerializer,
    EvaluateAllCombinationsSerializer,
    AllCombinationsEvaluationResultSerializer,
)
from .services import CombinationEvaluator
from apps.market_data.models import TradingPair, OHLCV
from apps.indicators.services import IndicatorEngine


class CombinationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Combination CRUD operations.

    list: GET /api/v1/combinations/combinations/
    create: POST /api/v1/combinations/combinations/
    retrieve: GET /api/v1/combinations/combinations/{id}/
    update: PUT /api/v1/combinations/combinations/{id}/
    partial_update: PATCH /api/v1/combinations/combinations/{id}/
    destroy: DELETE /api/v1/combinations/combinations/{id}/
    """

    queryset = Combination.objects.filter(is_active=True)
    serializer_class = CombinationSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'name']
    search_fields = ['name', 'display_name', 'description']
    ordering_fields = ['name', 'win_rate', 'risk_reward_ratio', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return CombinationListSerializer
        return CombinationSerializer

    @action(detail=True, methods=['get'])
    def info(self, request, pk=None):
        """
        Get detailed information about a combination.

        GET /api/v1/combinations/combinations/{id}/info/
        """
        combination = self.get_object()
        serializer = CombinationSerializer(combination)
        return Response(serializer.data)


class CombinationResultViewSet(viewsets.ModelViewSet):
    """
    API endpoint for CombinationResult CRUD operations.

    list: GET /api/v1/combinations/results/
    retrieve: GET /api/v1/combinations/results/{id}/
    """

    queryset = CombinationResult.objects.select_related(
        'combination', 'trading_pair'
    ).order_by('-evaluated_at')
    serializer_class = CombinationResultSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['combination', 'trading_pair', 'signal', 'timeframe']
    ordering_fields = ['evaluated_at', 'confidence', 'created_at']
    ordering = ['-evaluated_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return CombinationResultListSerializer
        return CombinationResultSerializer


class EvaluateCombinationAPIView(APIView):
    """
    Evaluate a single combination for a trading pair.

    POST /api/v1/combinations/evaluate/
    """

    def post(self, request):
        serializer = EvaluateCombinationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        combination_name = serializer.validated_data['combination_name']
        trading_pair_id = serializer.validated_data['trading_pair_id']
        timeframe = serializer.validated_data['timeframe']

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

        # Evaluate
        evaluator = CombinationEvaluator()
        result = evaluator.evaluate_single(combination_name, ohlcv_data)

        if result is None:
            return Response(
                {'error': f'Combination not found: {combination_name}'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(result)


class EvaluateAllCombinationsAPIView(APIView):
    """
    Evaluate all 8 combinations for a trading pair.

    POST /api/v1/combinations/evaluate-all/
    """

    def post(self, request):
        serializer = EvaluateAllCombinationsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        trading_pair_id = serializer.validated_data['trading_pair_id']
        timeframe = serializer.validated_data['timeframe']

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

        # Evaluate all combinations
        evaluator = CombinationEvaluator()
        results = evaluator.evaluate_all(ohlcv_data)

        # Save results to database
        for combo_name, combo_result in results['details'].items():
            try:
                combination = Combination.objects.get(name=combo_name)
                CombinationResult.objects.create(
                    combination=combination,
                    trading_pair=trading_pair,
                    timeframe=timeframe,
                    signal=combo_result['signal'],
                    confidence=combo_result['confidence'],
                    criteria_met=combo_result['criteria_met'],
                    criteria_details=combo_result.get('criteria_details', {}),
                    indicator_values=combo_result.get('indicator_values', {}),
                )
            except Combination.DoesNotExist:
                pass

        return Response(results)


class CombinationInfoAPIView(APIView):
    """
    Get information about all available combinations.

    GET /api/v1/combinations/info/
    """

    def get(self, request):
        evaluator = CombinationEvaluator()
        info = evaluator.get_combination_info()
        return Response(info)
