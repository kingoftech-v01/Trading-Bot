"""
Market Data Admin - Django admin configuration.

Registers models for admin interface:
- Exchange
- TradingPair
- OHLCV
- CorrelationMatrix
"""

from django.contrib import admin
from apps.core.admin import BaseModelAdmin
from .models import Exchange, TradingPair, OHLCV, CorrelationMatrix


@admin.register(Exchange)
class ExchangeAdmin(BaseModelAdmin):
    """Admin for Exchange model."""
    list_display = ['name', 'api_type', 'is_enabled', 'rate_limit', 'created_at']
    list_filter = ['api_type', 'is_enabled', 'is_active']
    search_fields = ['name']
    ordering = ['name']


@admin.register(TradingPair)
class TradingPairAdmin(BaseModelAdmin):
    """Admin for TradingPair model."""
    list_display = [
        'symbol', 'display_symbol', 'exchange', 'is_forex',
        'pip_value', 'is_active', 'created_at'
    ]
    list_filter = ['exchange', 'is_forex', 'is_active']
    search_fields = ['symbol', 'base_currency', 'quote_currency']
    ordering = ['symbol']
    raw_id_fields = ['exchange']

    def display_symbol(self, obj):
        return obj.display_symbol
    display_symbol.short_description = 'Display Symbol'


@admin.register(OHLCV)
class OHLCVAdmin(admin.ModelAdmin):
    """Admin for OHLCV model."""
    list_display = [
        'trading_pair', 'timeframe', 'timestamp',
        'open', 'high', 'low', 'close', 'volume'
    ]
    list_filter = ['trading_pair', 'timeframe']
    search_fields = ['trading_pair__symbol']
    ordering = ['-timestamp']
    raw_id_fields = ['trading_pair']
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        """Disable manual addition - data should come from API."""
        return False


@admin.register(CorrelationMatrix)
class CorrelationMatrixAdmin(admin.ModelAdmin):
    """Admin for CorrelationMatrix model."""
    list_display = [
        'primary_pair', 'secondary_pair', 'timeframe',
        'correlation_value', 'calculation_date'
    ]
    list_filter = ['timeframe', 'calculation_date']
    search_fields = ['primary_pair__symbol', 'secondary_pair__symbol']
    ordering = ['-calculation_date']
    raw_id_fields = ['primary_pair', 'secondary_pair']
    date_hierarchy = 'calculation_date'
