"""
Models for the orders app.
"""

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.core.models import BaseModel, TimeframeMixin


class Order(BaseModel, TimeframeMixin):
    """Order model for trade execution."""

    ORDER_TYPE_CHOICES = [
        ('market', 'Market'),
        ('limit', 'Limit'),
        ('stop', 'Stop'),
        ('stop_limit', 'Stop Limit'),
    ]

    SIDE_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('open', 'Open'),
        ('filled', 'Filled'),
        ('partially_filled', 'Partially Filled'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]

    signal = models.ForeignKey(
        'signals.Signal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
    )
    trading_pair = models.ForeignKey(
        'market_data.TradingPair',
        on_delete=models.CASCADE,
        related_name='orders',
    )
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default='market')
    side = models.CharField(max_length=10, choices=SIDE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Prices
    price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    stop_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    stop_loss = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    take_profit = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)

    # Quantities
    quantity = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(Decimal('0'))])
    filled_quantity = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0'))
    average_fill_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)

    # Exchange info
    exchange_order_id = models.CharField(max_length=100, blank=True)
    exchange = models.CharField(max_length=50, blank=True)

    # Timestamps
    submitted_at = models.DateTimeField(null=True, blank=True)
    filled_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    metadata = models.JSONField(default=dict)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['trading_pair', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.side.upper()} {self.quantity} {self.trading_pair.symbol} @ {self.price or 'MARKET'}"

    @property
    def is_filled(self):
        return self.status == 'filled'

    @property
    def remaining_quantity(self):
        return self.quantity - self.filled_quantity


class Trade(BaseModel, TimeframeMixin):
    """Completed trade with P&L."""

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]

    CLOSE_REASON_CHOICES = [
        ('take_profit', 'Take Profit'),
        ('stop_loss', 'Stop Loss'),
        ('manual', 'Manual'),
        ('signal', 'Signal'),
        ('expired', 'Expired'),
    ]

    signal = models.ForeignKey(
        'signals.Signal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trades',
    )
    trading_pair = models.ForeignKey(
        'market_data.TradingPair',
        on_delete=models.CASCADE,
        related_name='trades',
    )
    entry_order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        related_name='entry_trades',
    )
    exit_order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exit_trades',
    )

    side = models.CharField(max_length=10, choices=[('long', 'Long'), ('short', 'Short')])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    # Entry
    entry_price = models.DecimalField(max_digits=20, decimal_places=8)
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    stop_loss = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    take_profit = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)

    # Exit
    exit_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    close_reason = models.CharField(max_length=20, choices=CLOSE_REASON_CHOICES, null=True, blank=True)

    # P&L
    realized_pnl = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    realized_pnl_percent = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    fees = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0'))

    # Timestamps
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    metadata = models.JSONField(default=dict)

    class Meta:
        verbose_name = 'Trade'
        verbose_name_plural = 'Trades'
        ordering = ['-opened_at']

    def __str__(self):
        return f"{self.side.upper()} {self.trading_pair.symbol} - {self.status}"

    @property
    def is_profitable(self):
        return self.realized_pnl and self.realized_pnl > 0

    def calculate_pnl(self):
        """Calculate P&L when closing trade."""
        if not self.exit_price:
            return None

        if self.side == 'long':
            pnl = (self.exit_price - self.entry_price) * self.quantity
        else:
            pnl = (self.entry_price - self.exit_price) * self.quantity

        pnl -= self.fees
        self.realized_pnl = pnl

        entry_value = self.entry_price * self.quantity
        if entry_value > 0:
            self.realized_pnl_percent = (pnl / entry_value) * 100

        return pnl


class Position(BaseModel):
    """Current open position."""

    trading_pair = models.ForeignKey(
        'market_data.TradingPair',
        on_delete=models.CASCADE,
        related_name='positions',
    )
    side = models.CharField(max_length=10, choices=[('long', 'Long'), ('short', 'Short')])
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    average_entry_price = models.DecimalField(max_digits=20, decimal_places=8)
    current_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    stop_loss = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    take_profit = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    unrealized_pnl = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = 'Position'
        verbose_name_plural = 'Positions'
        unique_together = ['trading_pair', 'side']

    def __str__(self):
        return f"{self.side.upper()} {self.quantity} {self.trading_pair.symbol}"

    def update_pnl(self, current_price: Decimal):
        """Update unrealized P&L."""
        self.current_price = current_price
        if self.side == 'long':
            self.unrealized_pnl = (current_price - self.average_entry_price) * self.quantity
        else:
            self.unrealized_pnl = (self.average_entry_price - current_price) * self.quantity
        self.save(update_fields=['current_price', 'unrealized_pnl'])
