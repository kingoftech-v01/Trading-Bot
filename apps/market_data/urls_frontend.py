"""
Market Data App Frontend URLs - HTML routing.

URL Namespaces:
- Frontend: frontend:market_data:view_name
"""

from django.urls import path
from . import views_frontend

app_name = 'market_data'

urlpatterns = [
    # Dashboard
    path('', views_frontend.data_dashboard, name='dashboard'),

    # Exchanges
    path('exchanges/', views_frontend.exchange_list, name='exchange_list'),
    path('exchanges/<uuid:pk>/', views_frontend.exchange_detail, name='exchange_detail'),

    # Trading Pairs
    path('trading-pairs/', views_frontend.trading_pair_list, name='trading_pair_list'),
    path('trading-pairs/create/', views_frontend.trading_pair_create, name='trading_pair_create'),
    path('trading-pairs/<uuid:pk>/', views_frontend.trading_pair_detail, name='trading_pair_detail'),

    # Charts
    path('chart/<uuid:trading_pair_id>/', views_frontend.ohlcv_chart, name='ohlcv_chart'),
]
