"""URL configuration for the backtesting app."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views_api import BacktestRunViewSet, CreateBacktestAPIView
from .views_frontend import BacktestListView, BacktestDetailView, BacktestDashboardView

router = DefaultRouter()
router.register(r'backtests', BacktestRunViewSet, basename='backtest')

api_urlpatterns = [
    path('', include(router.urls)),
    path('create/', CreateBacktestAPIView.as_view(), name='create'),
]

frontend_urlpatterns = [
    path('', BacktestDashboardView.as_view(), name='dashboard'),
    path('list/', BacktestListView.as_view(), name='backtest_list'),
    path('<uuid:pk>/', BacktestDetailView.as_view(), name='backtest_detail'),
]

urlpatterns = frontend_urlpatterns
