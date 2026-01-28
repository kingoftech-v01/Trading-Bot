"""API Views for the backtesting app."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BacktestRun, BacktestTrade, BacktestResult
from .serializers import (
    BacktestRunSerializer, BacktestTradeSerializer,
    BacktestResultSerializer, CreateBacktestSerializer,
)
from .services import Backtester
from apps.market_data.models import TradingPair


class BacktestRunViewSet(viewsets.ModelViewSet):
    queryset = BacktestRun.objects.select_related('trading_pair').order_by('-created_at')
    serializer_class = BacktestRunSerializer

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        backtest = self.get_object()
        if backtest.status not in ['pending', 'failed']:
            return Response({'error': 'Cannot run backtest in current state'}, status=status.HTTP_400_BAD_REQUEST)

        from .tasks import run_backtest_task
        run_backtest_task.delay(str(backtest.id))

        return Response({'message': 'Backtest started', 'backtest_id': str(backtest.id)})

    @action(detail=True, methods=['get'])
    def trades(self, request, pk=None):
        backtest = self.get_object()
        trades = BacktestTrade.objects.filter(backtest_run=backtest)
        serializer = BacktestTradeSerializer(trades, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        backtest = self.get_object()
        try:
            results = BacktestResult.objects.get(backtest_run=backtest)
            serializer = BacktestResultSerializer(results)
            return Response(serializer.data)
        except BacktestResult.DoesNotExist:
            return Response({'error': 'No results yet'}, status=status.HTTP_404_NOT_FOUND)


class CreateBacktestAPIView(APIView):
    def post(self, request):
        serializer = CreateBacktestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            trading_pair = TradingPair.objects.get(id=data['trading_pair_id'])
        except TradingPair.DoesNotExist:
            return Response({'error': 'Trading pair not found'}, status=status.HTTP_404_NOT_FOUND)

        backtest = BacktestRun.objects.create(
            name=data['name'],
            trading_pair=trading_pair,
            timeframe=data.get('timeframe', '1h'),
            start_date=data['start_date'],
            end_date=data['end_date'],
            initial_balance=data.get('initial_balance', 10000),
            risk_per_trade=data.get('risk_per_trade', 0.01),
            voting_threshold=data.get('voting_threshold', 5),
        )

        return Response(BacktestRunSerializer(backtest).data, status=status.HTTP_201_CREATED)
