"""API Views for the orders app."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, Trade, Position
from .serializers import OrderSerializer, TradeSerializer, PositionSerializer, CreateOrderSerializer
from .services import OrderExecutor, PositionManager, TradeLogger
from apps.market_data.models import TradingPair


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related('trading_pair').order_by('-created_at')
    serializer_class = OrderSerializer

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        executor = OrderExecutor()
        result = executor.cancel_order(order)
        if result.success:
            return Response(result.data)
        return Response({'error': result.error}, status=status.HTTP_400_BAD_REQUEST)


class TradeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Trade.objects.select_related('trading_pair').order_by('-opened_at')
    serializer_class = TradeSerializer

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        days = int(request.query_params.get('days', 30))
        logger = TradeLogger()
        result = logger.get_trade_statistics(days=days)
        if result.success:
            return Response(result.data)
        return Response({'error': result.error}, status=status.HTTP_400_BAD_REQUEST)


class PositionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Position.objects.filter(is_active=True).select_related('trading_pair')
    serializer_class = PositionSerializer

    @action(detail=False, methods=['get'])
    def summary(self, request):
        manager = PositionManager()
        result = manager.get_position_summary()
        if result.success:
            return Response(result.data)
        return Response({'error': result.error}, status=status.HTTP_400_BAD_REQUEST)


class CreateOrderAPIView(APIView):
    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            trading_pair = TradingPair.objects.get(id=data['trading_pair_id'])
        except TradingPair.DoesNotExist:
            return Response({'error': 'Trading pair not found'}, status=status.HTTP_404_NOT_FOUND)

        executor = OrderExecutor()
        result = executor.create_order(
            trading_pair=trading_pair,
            side=data['side'],
            quantity=data['quantity'],
            order_type=data.get('order_type', 'market'),
            price=data.get('price'),
            stop_loss=data.get('stop_loss'),
            take_profit=data.get('take_profit'),
        )

        if result.success:
            return Response(result.data, status=status.HTTP_201_CREATED)
        return Response({'error': result.error}, status=status.HTTP_400_BAD_REQUEST)
