"""Models for the backtesting app."""

from django.db import models
from decimal import Decimal
from apps.core.models import BaseModel, TimeframeMixin


class BacktestRun(BaseModel, TimeframeMixin):
    """A single backtest execution."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    trading_pair = models.ForeignKey(
        'market_data.TradingPair',
        on_delete=models.CASCADE,
        related_name='backtest_runs',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Date range
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    # Configuration
    initial_balance = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('10000'))
    risk_per_trade = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.01'))
    voting_threshold = models.IntegerField(default=5)
    min_confluence = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('50'))

    # Execution
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    # Results summary
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    final_balance = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    total_return = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    profit_factor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_drawdown = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    sharpe_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    class Meta:
        verbose_name = 'Backtest Run'
        verbose_name_plural = 'Backtest Runs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.trading_pair.symbol}"


class BacktestTrade(BaseModel):
    """Individual trade within a backtest."""

    backtest_run = models.ForeignKey(
        BacktestRun,
        on_delete=models.CASCADE,
        related_name='trades',
    )
    signal_type = models.CharField(max_length=10, choices=[('buy', 'Buy'), ('sell', 'Sell')])
    entry_time = models.DateTimeField()
    exit_time = models.DateTimeField(null=True, blank=True)
    entry_price = models.DecimalField(max_digits=20, decimal_places=8)
    exit_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    stop_loss = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    take_profit = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)

    # Results
    pnl = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    pnl_percent = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    exit_reason = models.CharField(max_length=50, blank=True)

    # Signal details
    vote_count = models.IntegerField(default=0)
    confluence_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    voting_combinations = models.JSONField(default=list)

    class Meta:
        verbose_name = 'Backtest Trade'
        verbose_name_plural = 'Backtest Trades'
        ordering = ['entry_time']

    def __str__(self):
        return f"{self.signal_type.upper()} @ {self.entry_price}"


class BacktestResult(BaseModel):
    """Detailed results and metrics for a backtest."""

    backtest_run = models.OneToOneField(
        BacktestRun,
        on_delete=models.CASCADE,
        related_name='detailed_results',
    )

    # Returns
    total_return_pct = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    annualized_return = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    monthly_returns = models.JSONField(default=list)

    # Risk metrics
    max_drawdown_pct = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    max_drawdown_duration = models.IntegerField(null=True, blank=True)  # days
    sharpe_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    sortino_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    calmar_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    # Trade statistics
    avg_trade_duration = models.DurationField(null=True, blank=True)
    avg_win = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    avg_loss = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    largest_win = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    largest_loss = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    consecutive_wins = models.IntegerField(null=True, blank=True)
    consecutive_losses = models.IntegerField(null=True, blank=True)

    # Combination performance
    combination_performance = models.JSONField(default=dict)

    # Equity curve
    equity_curve = models.JSONField(default=list)

    class Meta:
        verbose_name = 'Backtest Result'
        verbose_name_plural = 'Backtest Results'

    def __str__(self):
        return f"Results for {self.backtest_run.name}"
