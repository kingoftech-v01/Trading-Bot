"""Frontend Views for the orders app."""

from django.views.generic import ListView, DetailView, TemplateView

from .models import Order, Trade, Position
from .services import TradeLogger, PositionManager


class OrderListView(ListView):
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 50


class OrderDetailView(DetailView):
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'


class TradeListView(ListView):
    model = Trade
    template_name = 'orders/trade_list.html'
    context_object_name = 'trades'
    paginate_by = 50


class TradeDetailView(DetailView):
    model = Trade
    template_name = 'orders/trade_detail.html'
    context_object_name = 'trade'


class PositionListView(ListView):
    model = Position
    template_name = 'orders/position_list.html'
    context_object_name = 'positions'

    def get_queryset(self):
        return Position.objects.filter(is_active=True).select_related('trading_pair')


class TradingDashboardView(TemplateView):
    template_name = 'orders/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        logger = TradeLogger()
        stats_result = logger.get_trade_statistics()
        context['statistics'] = stats_result.data if stats_result.success else None
        context['recent_trades'] = logger.get_recent_trades(10)

        manager = PositionManager()
        positions_result = manager.get_position_summary()
        context['positions'] = positions_result.data if positions_result.success else None

        return context
