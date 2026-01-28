"""
Admin configuration for the risk_management app.
"""

from django.contrib import admin
from .models import RiskProfile, PositionSizeCalculation, DailyRiskTracker


@admin.register(RiskProfile)
class RiskProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_balance', 'risk_per_trade', 'min_risk_reward', 'is_default', 'is_active']
    list_filter = ['is_default', 'is_active']
    search_fields = ['name']


@admin.register(PositionSizeCalculation)
class PositionSizeCalculationAdmin(admin.ModelAdmin):
    list_display = ['trading_pair', 'direction', 'position_size', 'risk_amount', 'created_at']
    list_filter = ['direction', 'risk_profile']
    date_hierarchy = 'created_at'


@admin.register(DailyRiskTracker)
class DailyRiskTrackerAdmin(admin.ModelAdmin):
    list_display = ['risk_profile', 'date', 'total_risk_taken', 'total_trades', 'is_limit_reached']
    list_filter = ['is_limit_reached', 'risk_profile']
    date_hierarchy = 'date'
