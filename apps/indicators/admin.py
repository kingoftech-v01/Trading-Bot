"""
Indicators Admin - Django admin configuration.
"""

from django.contrib import admin
from apps.core.admin import BaseModelAdmin
from .models import IndicatorType, IndicatorConfig, IndicatorResult


@admin.register(IndicatorType)
class IndicatorTypeAdmin(BaseModelAdmin):
    list_display = ['name', 'display_name', 'is_active']
    search_fields = ['name', 'display_name']


@admin.register(IndicatorConfig)
class IndicatorConfigAdmin(BaseModelAdmin):
    list_display = ['indicator_type', 'trading_pair', 'timeframe', 'is_enabled']
    list_filter = ['indicator_type', 'timeframe', 'is_enabled']
    raw_id_fields = ['indicator_type', 'trading_pair']


@admin.register(IndicatorResult)
class IndicatorResultAdmin(admin.ModelAdmin):
    list_display = ['config', 'timestamp', 'created_at']
    list_filter = ['config__indicator_type', 'timestamp']
    raw_id_fields = ['config', 'ohlcv']
    date_hierarchy = 'timestamp'
