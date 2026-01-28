"""
Models for the risk_management app.

Handles risk profiles, position size calculations, and risk metrics.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from apps.core.models import BaseModel


class RiskProfile(BaseModel):
    """
    Risk profile configuration.

    Defines risk parameters for the trading account.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Profile name"
    )
    description = models.TextField(
        blank=True,
        help_text="Profile description"
    )
    account_balance = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('10000.00'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Account balance in base currency"
    )
    base_currency = models.CharField(
        max_length=10,
        default='USD',
        help_text="Account base currency"
    )
    risk_per_trade = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.01'),
        validators=[
            MinValueValidator(Decimal('0.001')),
            MaxValueValidator(Decimal('0.10'))
        ],
        help_text="Risk per trade as decimal (0.01 = 1%)"
    )
    max_daily_risk = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.05'),
        validators=[
            MinValueValidator(Decimal('0.01')),
            MaxValueValidator(Decimal('0.20'))
        ],
        help_text="Maximum daily risk as decimal (0.05 = 5%)"
    )
    max_open_positions = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text="Maximum number of open positions"
    )
    max_position_size = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.10'),
        validators=[
            MinValueValidator(Decimal('0.01')),
            MaxValueValidator(Decimal('0.50'))
        ],
        help_text="Maximum position size as decimal of balance"
    )
    min_risk_reward = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('3.00'),
        validators=[MinValueValidator(Decimal('1.00'))],
        help_text="Minimum risk/reward ratio required"
    )
    use_trailing_stop = models.BooleanField(
        default=False,
        help_text="Enable trailing stop loss"
    )
    trailing_stop_distance = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Trailing stop distance as decimal"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the default profile"
    )

    class Meta:
        verbose_name = 'Risk Profile'
        verbose_name_plural = 'Risk Profiles'
        ordering = ['-is_default', 'name']

    def __str__(self):
        return f"{self.name} ({self.risk_per_trade*100:.1f}% risk)"

    def save(self, *args, **kwargs):
        # Ensure only one default profile
        if self.is_default:
            RiskProfile.objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @property
    def max_risk_amount(self):
        """Maximum risk amount per trade."""
        return self.account_balance * self.risk_per_trade

    @property
    def max_daily_risk_amount(self):
        """Maximum daily risk amount."""
        return self.account_balance * self.max_daily_risk


class PositionSizeCalculation(BaseModel):
    """
    Record of position size calculations.

    Stores the calculation details for audit and analysis.
    """

    risk_profile = models.ForeignKey(
        RiskProfile,
        on_delete=models.CASCADE,
        related_name='calculations',
        help_text="Risk profile used"
    )
    signal = models.ForeignKey(
        'signals.Signal',
        on_delete=models.CASCADE,
        related_name='position_calculations',
        null=True,
        blank=True,
        help_text="Associated signal"
    )
    trading_pair = models.ForeignKey(
        'market_data.TradingPair',
        on_delete=models.CASCADE,
        related_name='position_calculations',
        help_text="Trading pair"
    )
    entry_price = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="Entry price"
    )
    stop_loss = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="Stop loss price"
    )
    take_profit = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Take profit price"
    )
    risk_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Risk amount in base currency"
    )
    position_size = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="Calculated position size"
    )
    position_value = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Position value in base currency"
    )
    risk_reward_ratio = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Risk/reward ratio"
    )
    risk_percent = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        help_text="Risk as percent of balance"
    )
    direction = models.CharField(
        max_length=10,
        choices=[('buy', 'Buy'), ('sell', 'Sell')],
        help_text="Trade direction"
    )
    calculation_details = models.JSONField(
        default=dict,
        help_text="Detailed calculation breakdown"
    )

    class Meta:
        verbose_name = 'Position Size Calculation'
        verbose_name_plural = 'Position Size Calculations'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.trading_pair.symbol} - {self.position_size} @ {self.entry_price}"


class DailyRiskTracker(BaseModel):
    """
    Tracks daily risk exposure.

    Used to ensure daily risk limits are not exceeded.
    """

    risk_profile = models.ForeignKey(
        RiskProfile,
        on_delete=models.CASCADE,
        related_name='daily_trackers',
        help_text="Risk profile"
    )
    date = models.DateField(
        help_text="Trading date"
    )
    total_risk_taken = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Total risk taken today"
    )
    total_trades = models.IntegerField(
        default=0,
        help_text="Number of trades today"
    )
    realized_pnl = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Realized P&L for the day"
    )
    max_drawdown = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Maximum drawdown for the day"
    )
    is_limit_reached = models.BooleanField(
        default=False,
        help_text="Whether daily limit was reached"
    )

    class Meta:
        verbose_name = 'Daily Risk Tracker'
        verbose_name_plural = 'Daily Risk Trackers'
        ordering = ['-date']
        unique_together = ['risk_profile', 'date']

    def __str__(self):
        return f"{self.risk_profile.name} - {self.date}"

    @property
    def remaining_risk(self):
        """Remaining risk for the day."""
        max_risk = self.risk_profile.max_daily_risk_amount
        return max(Decimal('0'), max_risk - self.total_risk_taken)

    @property
    def risk_utilization(self):
        """Risk utilization percentage."""
        max_risk = self.risk_profile.max_daily_risk_amount
        if max_risk > 0:
            return (self.total_risk_taken / max_risk) * 100
        return Decimal('0')
