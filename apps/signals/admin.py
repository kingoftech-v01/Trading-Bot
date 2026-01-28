"""
Admin configuration for the signals app.
"""

from django.contrib import admin
from .models import Vote, SignalSession, Signal, ConfluenceScore


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    """Admin interface for Vote model."""

    list_display = [
        'combination',
        'trading_pair',
        'signal',
        'confidence',
        'created_at',
    ]
    list_filter = ['signal', 'combination', 'trading_pair', 'timeframe']
    search_fields = [
        'combination__name',
        'combination__display_name',
        'trading_pair__symbol',
    ]
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('id', 'combination', 'trading_pair', 'signal_session')
        }),
        ('Vote Details', {
            'fields': ('timeframe', 'signal', 'confidence')
        }),
        ('Criteria', {
            'fields': ('criteria_met', 'indicator_values'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'combination', 'trading_pair', 'signal_session'
        )


@admin.register(SignalSession)
class SignalSessionAdmin(admin.ModelAdmin):
    """Admin interface for SignalSession model."""

    list_display = [
        'trading_pair',
        'timeframe',
        'final_signal',
        'buy_votes',
        'sell_votes',
        'neutral_votes',
        'confluence_score',
        'evaluated_at',
    ]
    list_filter = ['final_signal', 'timeframe', 'trading_pair']
    search_fields = ['trading_pair__symbol']
    ordering = ['-evaluated_at']
    readonly_fields = ['id', 'created_at', 'updated_at', 'evaluated_at']
    date_hierarchy = 'evaluated_at'

    fieldsets = (
        (None, {
            'fields': ('id', 'trading_pair', 'timeframe')
        }),
        ('Voting Results', {
            'fields': (
                'final_signal',
                'buy_votes',
                'sell_votes',
                'neutral_votes',
                'voting_threshold',
            )
        }),
        ('Scores', {
            'fields': ('confluence_score', 'average_confidence')
        }),
        ('Timestamps', {
            'fields': ('evaluated_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('trading_pair')


@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    """Admin interface for Signal model."""

    list_display = [
        'trading_pair',
        'signal',
        'status',
        'vote_count',
        'confluence_score',
        'confidence',
        'entry_price',
        'created_at',
    ]
    list_filter = ['signal', 'status', 'timeframe', 'trading_pair']
    search_fields = ['trading_pair__symbol']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at', 'executed_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('id', 'session', 'trading_pair', 'timeframe')
        }),
        ('Signal Details', {
            'fields': (
                'signal',
                'status',
                'vote_count',
                'confluence_score',
                'confidence',
            )
        }),
        ('Trade Levels', {
            'fields': (
                'entry_price',
                'stop_loss',
                'take_profit',
                'risk_reward_ratio',
            )
        }),
        ('Timing', {
            'fields': ('expires_at', 'executed_at')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_executed', 'mark_cancelled', 'mark_expired']

    def mark_executed(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='executed')
        self.message_user(request, f'{updated} signals marked as executed.')
    mark_executed.short_description = 'Mark selected signals as executed'

    def mark_cancelled(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='cancelled')
        self.message_user(request, f'{updated} signals cancelled.')
    mark_cancelled.short_description = 'Cancel selected signals'

    def mark_expired(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='expired')
        self.message_user(request, f'{updated} signals marked as expired.')
    mark_expired.short_description = 'Mark selected signals as expired'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'trading_pair', 'session'
        )


@admin.register(ConfluenceScore)
class ConfluenceScoreAdmin(admin.ModelAdmin):
    """Admin interface for ConfluenceScore model."""

    list_display = [
        'trading_pair',
        'timeframe',
        'total_score',
        'vote_weight_score',
        'confidence_score',
        'created_at',
    ]
    list_filter = ['timeframe', 'trading_pair']
    search_fields = ['trading_pair__symbol']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('id', 'session', 'trading_pair', 'timeframe')
        }),
        ('Scores', {
            'fields': (
                'total_score',
                'vote_weight_score',
                'confidence_score',
                'win_rate_score',
                'risk_reward_score',
                'indicator_alignment_score',
            )
        }),
        ('Breakdown', {
            'fields': ('scoring_breakdown',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'trading_pair', 'session'
        )
