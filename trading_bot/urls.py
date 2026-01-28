"""
Trading Bot URL Configuration.

This module configures the root URL routing for the trading bot platform.
Following the URL_AND_VIEW_CONVENTIONS.md dual-layer architecture:
- Frontend URLs: /app-name/
- API URLs: /api/v1/app-name/
"""

from django.contrib import admin
from django.urls import path, include

# API v1 URL patterns
api_v1_patterns = [
    path('market-data/', include('apps.market_data.urls', namespace='market_data')),
    path('indicators/', include('apps.indicators.urls', namespace='indicators')),
    path('combinations/', include('apps.combinations.urls', namespace='combinations')),
    path('signals/', include('apps.signals.urls', namespace='signals')),
    path('risk-management/', include('apps.risk_management.urls', namespace='risk_management')),
    path('orders/', include('apps.orders.urls', namespace='orders')),
    path('backtesting/', include('apps.backtesting.urls', namespace='backtesting')),
    path('monitoring/', include('apps.monitoring.urls', namespace='monitoring')),
    path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
]

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API v1
    path('api/v1/', include((api_v1_patterns, 'api'), namespace='api-v1')),

    # Frontend URLs
    path('', include('apps.dashboard.urls_frontend', namespace='dashboard-frontend')),
    path('market-data/', include('apps.market_data.urls_frontend', namespace='market_data-frontend')),
    path('indicators/', include('apps.indicators.urls_frontend', namespace='indicators-frontend')),
    path('combinations/', include('apps.combinations.urls_frontend', namespace='combinations-frontend')),
    path('signals/', include('apps.signals.urls_frontend', namespace='signals-frontend')),
    path('risk-management/', include('apps.risk_management.urls_frontend', namespace='risk_management-frontend')),
    path('orders/', include('apps.orders.urls_frontend', namespace='orders-frontend')),
    path('backtesting/', include('apps.backtesting.urls_frontend', namespace='backtesting-frontend')),
    path('monitoring/', include('apps.monitoring.urls_frontend', namespace='monitoring-frontend')),
]
