"""
Indicators API Views - REST API endpoints.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.views_api import BaseModelViewSet
from apps.market_data.models import TradingPair, OHLCV
from .models import IndicatorType, IndicatorConfig, IndicatorResult
from .serializers import (
    IndicatorTypeSerializer, IndicatorConfigSerializer,
    IndicatorResultSerializer, CalculateIndicatorSerializer
)
from .services import IndicatorEngine


class IndicatorTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IndicatorType.objects.all()
    serializer_class = IndicatorTypeSerializer


class IndicatorConfigViewSet(BaseModelViewSet):
    queryset = IndicatorConfig.objects.select_related('indicator_type', 'trading_pair')
    serializer_class = IndicatorConfigSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['indicator_type', 'trading_pair', 'timeframe', 'is_enabled']


class IndicatorResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IndicatorResult.objects.select_related('config')
    serializer_class = IndicatorResultSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['config', 'timestamp']


class CalculateIndicatorsAPIView(APIView):
    """
    Calculate indicators for a trading pair.

    POST /api/v1/indicators/calculate/
    """

    def post(self, request):
        serializer = CalculateIndicatorSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        trading_pair_id = data['trading_pair_id']
        timeframe = data['timeframe']
        indicators = data.get('indicators')
        limit = data['limit']

        try:
            pair = TradingPair.objects.get(id=trading_pair_id, is_active=True)
        except TradingPair.DoesNotExist:
            return Response(
                {'error': 'Trading pair not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get OHLCV data
        ohlcv_qs = OHLCV.objects.filter(
            trading_pair=pair,
            timeframe=timeframe
        ).order_by('-timestamp')[:limit]

        ohlcv_data = [
            {
                'timestamp': o.timestamp,
                'open': float(o.open),
                'high': float(o.high),
                'low': float(o.low),
                'close': float(o.close),
                'volume': float(o.volume),
            }
            for o in reversed(list(ohlcv_qs))
        ]

        if not ohlcv_data:
            return Response(
                {'error': 'No OHLCV data available'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Calculate indicators
        engine = IndicatorEngine()
        results = engine.calculate_all(ohlcv_data, indicators)

        return Response({
            'trading_pair': pair.symbol,
            'timeframe': timeframe,
            'data_points': len(ohlcv_data),
            'indicators': results,
        })
