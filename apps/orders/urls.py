"""URL configuration for the orders app."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views_api import OrderViewSet, TradeViewSet, PositionViewSet, CreateOrderAPIView
from .views_frontend import (
    OrderListView, OrderDetailView,
    TradeListView, TradeDetailView,
    PositionListView, TradingDashboardView,
)

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'trades', TradeViewSet, basename='trade')
router.register(r'positions', PositionViewSet, basename='position')

api_urlpatterns = [
    path('', include(router.urls)),
    path('create-order/', CreateOrderAPIView.as_view(), name='create-order'),
]

frontend_urlpatterns = [
    path('', TradingDashboardView.as_view(), name='dashboard'),
    path('orders/', OrderListView.as_view(), name='order_list'),
    path('orders/<uuid:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('trades/', TradeListView.as_view(), name='trade_list'),
    path('trades/<uuid:pk>/', TradeDetailView.as_view(), name='trade_detail'),
    path('positions/', PositionListView.as_view(), name='position_list'),
]

urlpatterns = frontend_urlpatterns
