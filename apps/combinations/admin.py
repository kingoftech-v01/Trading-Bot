"""
Admin configuration for the combinations app.
"""

from django.contrib import admin
from .models import Combination, CombinationResult


@admin.register(Combination)
class CombinationAdmin(admin.ModelAdmin):
    """Admin interface for Combination model."""

    list_display = [
        'name',
        'display_name',
        'win_rate',
        'risk_reward_ratio',
        'expected_frequency',
        'is_active',
        'created_at',
    ]
    list_filter = ['is_active', 'win_rate', 'risk_reward_ratio']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'display_name', 'description')
        }),
        ('Performance Metrics', {
            'fields': ('win_rate', 'risk_reward_ratio', 'expected_frequency')
        }),
        ('Configuration', {
            'fields': ('required_indicators', 'buy_criteria', 'sell_criteria')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CombinationResult)
class CombinationResultAdmin(admin.ModelAdmin):
    """Admin interface for CombinationResult model."""

    list_display = [
        'combination',
        'trading_pair',
        'timeframe',
        'signal',
        'confidence',
        'evaluated_at',
    ]
    list_filter = ['signal', 'timeframe', 'combination', 'evaluated_at']
    search_fields = [
        'combination__name',
        'combination__display_name',
        'trading_pair__symbol',
    ]
    ordering = ['-evaluated_at']
    readonly_fields = ['id', 'created_at', 'evaluated_at']
    date_hierarchy = 'evaluated_at'

    fieldsets = (
        (None, {
            'fields': ('id', 'combination', 'trading_pair', 'timeframe')
        }),
        ('Evaluation Result', {
            'fields': ('signal', 'confidence', 'evaluated_at')
        }),
        ('Details', {
            'fields': ('criteria_met', 'criteria_details', 'indicator_values'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'combination', 'trading_pair'
        )
