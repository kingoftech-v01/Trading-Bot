"""
Market Data Models - OHLCV data storage and management.

This module provides models for:
- Exchange: Supported exchanges (CoinAPI, Binance, MT5)
- TradingPair: Trading pairs like EUR/USD, BTC/USD
- OHLCV: Candlestick data (Open, High, Low, Close, Volume)
- CorrelationMatrix: Cross-pair correlation data
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel, TimeframeMixin
from decimal import Decimal


class Exchange(BaseModel):
    """
    Supported exchanges for data collection.

    Examples: CoinAPI, Binance, MetaTrader 5
    """
    API_TYPE_REST = 'rest'
    API_TYPE_WEBSOCKET = 'websocket'
    API_TYPE_MT5 = 'mt5'

    API_TYPE_CHOICES = [
        (API_TYPE_REST, _('REST API')),
        (API_TYPE_WEBSOCKET, _('WebSocket')),
        (API_TYPE_MT5, _('MetaTrader 5')),
    ]

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Name')
    )
    api_type = models.CharField(
        max_length=50,
        choices=API_TYPE_CHOICES,
        default=API_TYPE_REST,
        verbose_name=_('API Type')
    )
    base_url = models.URLField(
        blank=True,
        verbose_name=_('Base URL')
    )
    is_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Is Enabled')
    )
    config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Configuration'),
        help_text=_('API keys and settings (stored encrypted in production)')
    )
    rate_limit = models.IntegerField(
        default=100,
        verbose_name=_('Rate Limit'),
        help_text=_('Maximum requests per minute')
    )

    class Meta:
        db_table = 'market_data_exchange'
        verbose_name = _('Exchange')
        verbose_name_plural = _('Exchanges')

    def __str__(self):
        return self.name


class TradingPair(BaseModel):
    """
    Trading pairs available for trading.

    Examples: EUR/USD, BTC/USD, GBP/USD
    """
    symbol = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Symbol'),
        help_text=_('Trading symbol (e.g., EURUSD, BTCUSD)')
    )
    base_currency = models.CharField(
        max_length=10,
        verbose_name=_('Base Currency'),
        help_text=_('Base currency (e.g., EUR, BTC)')
    )
    quote_currency = models.CharField(
        max_length=10,
        verbose_name=_('Quote Currency'),
        help_text=_('Quote currency (e.g., USD)')
    )
    exchange = models.ForeignKey(
        Exchange,
        on_delete=models.CASCADE,
        related_name='trading_pairs',
        verbose_name=_('Exchange')
    )
    pip_value = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=Decimal('0.0001'),
        verbose_name=_('Pip Value'),
        help_text=_('Value of one pip')
    )
    min_lot_size = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('0.01'),
        verbose_name=_('Minimum Lot Size')
    )
    max_lot_size = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('100.0'),
        verbose_name=_('Maximum Lot Size')
    )
    is_forex = models.BooleanField(
        default=True,
        verbose_name=_('Is Forex'),
        help_text=_('True for forex pairs, False for crypto')
    )

    class Meta:
        db_table = 'market_data_trading_pair'
        verbose_name = _('Trading Pair')
        verbose_name_plural = _('Trading Pairs')
        ordering = ['symbol']

    def __str__(self):
        return self.symbol

    @property
    def display_symbol(self) -> str:
        """Return formatted symbol (EUR/USD format)."""
        return f"{self.base_currency}/{self.quote_currency}"


class OHLCV(BaseModel, TimeframeMixin):
    """
    OHLCV (Open, High, Low, Close, Volume) candlestick data.

    Stores historical price data for technical analysis.
    """
    trading_pair = models.ForeignKey(
        TradingPair,
        on_delete=models.CASCADE,
        related_name='ohlcv_data',
        verbose_name=_('Trading Pair')
    )
    timestamp = models.DateTimeField(
        verbose_name=_('Timestamp'),
        help_text=_('Candle open time')
    )
    open = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        verbose_name=_('Open Price')
    )
    high = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        verbose_name=_('High Price')
    )
    low = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        verbose_name=_('Low Price')
    )
    close = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        verbose_name=_('Close Price')
    )
    volume = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        default=Decimal('0'),
        verbose_name=_('Volume')
    )

    class Meta:
        db_table = 'market_data_ohlcv'
        verbose_name = _('OHLCV')
        verbose_name_plural = _('OHLCV Data')
        unique_together = ['trading_pair', 'timeframe', 'timestamp']
        indexes = [
            models.Index(fields=['trading_pair', 'timeframe', 'timestamp']),
            models.Index(fields=['trading_pair', 'timeframe', '-timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.trading_pair.symbol} {self.timeframe} {self.timestamp}"

    @property
    def range(self) -> Decimal:
        """Return the candle range (high - low)."""
        return self.high - self.low

    @property
    def body(self) -> Decimal:
        """Return the candle body size (|close - open|)."""
        return abs(self.close - self.open)

    @property
    def is_bullish(self) -> bool:
        """Return True if candle is bullish (close > open)."""
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        """Return True if candle is bearish (close < open)."""
        return self.close < self.open


class CorrelationMatrix(BaseModel):
    """
    Cross-pair correlation data for multi-pair validation.

    Used to validate signals across correlated pairs.
    """
    primary_pair = models.ForeignKey(
        TradingPair,
        on_delete=models.CASCADE,
        related_name='primary_correlations',
        verbose_name=_('Primary Pair')
    )
    secondary_pair = models.ForeignKey(
        TradingPair,
        on_delete=models.CASCADE,
        related_name='secondary_correlations',
        verbose_name=_('Secondary Pair')
    )
    timeframe = models.CharField(
        max_length=10,
        verbose_name=_('Timeframe')
    )
    correlation_value = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        verbose_name=_('Correlation'),
        help_text=_('Correlation coefficient (-1 to +1)')
    )
    calculation_date = models.DateField(
        verbose_name=_('Calculation Date')
    )
    lookback_periods = models.IntegerField(
        default=50,
        verbose_name=_('Lookback Periods'),
        help_text=_('Number of periods used for calculation')
    )

    class Meta:
        db_table = 'market_data_correlation'
        verbose_name = _('Correlation')
        verbose_name_plural = _('Correlations')
        unique_together = ['primary_pair', 'secondary_pair', 'timeframe', 'calculation_date']

    def __str__(self):
        return f"{self.primary_pair.symbol} <-> {self.secondary_pair.symbol}: {self.correlation_value}"

    @property
    def is_strong_positive(self) -> bool:
        """Return True if correlation is strongly positive (> 0.7)."""
        return self.correlation_value > Decimal('0.7')

    @property
    def is_strong_negative(self) -> bool:
        """Return True if correlation is strongly negative (< -0.7)."""
        return self.correlation_value < Decimal('-0.7')
