"""
Market Data App URLs - API routing.

URL Namespaces:
- API: api:v1:market_data:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_api

# API Router
router = DefaultRouter()
router.register(r'exchanges', views_api.ExchangeViewSet, basename='exchange')
router.register(r'trading-pairs', views_api.TradingPairViewSet, basename='trading-pair')
router.register(r'ohlcv', views_api.OHLCVViewSet, basename='ohlcv')
router.register(r'correlations', views_api.CorrelationMatrixViewSet, basename='correlation')

app_name = 'market_data'

urlpatterns = [
    path('', include(router.urls)),
    path('fetch/', views_api.FetchDataAPIView.as_view(), name='fetch-data'),
]
