"""Admin configuration for the backtesting app."""

from django.contrib import admin
from .models import BacktestRun, BacktestTrade, BacktestResult


@admin.register(BacktestRun)
class BacktestRunAdmin(admin.ModelAdmin):
    list_display = ['name', 'trading_pair', 'status', 'total_trades', 'win_rate', 'total_return', 'created_at']
    list_filter = ['status', 'trading_pair']
    search_fields = ['name']
    date_hierarchy = 'created_at'


@admin.register(BacktestTrade)
class BacktestTradeAdmin(admin.ModelAdmin):
    list_display = ['backtest_run', 'signal_type', 'entry_price', 'exit_price', 'pnl', 'exit_reason']
    list_filter = ['signal_type', 'exit_reason']


@admin.register(BacktestResult)
class BacktestResultAdmin(admin.ModelAdmin):
    list_display = ['backtest_run', 'total_return_pct', 'max_drawdown_pct', 'sharpe_ratio']
