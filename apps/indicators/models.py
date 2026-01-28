"""
Indicators Models - Technical indicator storage.

This module provides models for:
- IndicatorType: Available indicator types
- IndicatorConfig: Configuration per pair/timeframe
- IndicatorResult: Calculated indicator values
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from apps.market_data.models import TradingPair, OHLCV


class IndicatorType(BaseModel):
    """
    Available indicator types.

    Defines the technical indicators available in the system.
    """
    INDICATOR_RSI = 'rsi'
    INDICATOR_MACD = 'macd'
    INDICATOR_ADX = 'adx'
    INDICATOR_STOCHASTIC = 'stochastic'
    INDICATOR_BOLLINGER = 'bollinger'
    INDICATOR_LINEAR_REGRESSION = 'linear_regression'
    INDICATOR_CCI = 'cci'
    INDICATOR_ATR = 'atr'
    INDICATOR_VOLUME_PROFILE = 'volume_profile'
    INDICATOR_SUPPORT_RESISTANCE = 'support_resistance'

    INDICATOR_CHOICES = [
        (INDICATOR_RSI, _('RSI - Relative Strength Index')),
        (INDICATOR_MACD, _('MACD - Moving Average Convergence Divergence')),
        (INDICATOR_ADX, _('ADX - Average Directional Index')),
        (INDICATOR_STOCHASTIC, _('Stochastic Oscillator')),
        (INDICATOR_BOLLINGER, _('Bollinger Bands')),
        (INDICATOR_LINEAR_REGRESSION, _('Linear Regression')),
        (INDICATOR_CCI, _('CCI - Commodity Channel Index')),
        (INDICATOR_ATR, _('ATR - Average True Range')),
        (INDICATOR_VOLUME_PROFILE, _('Volume Profile')),
        (INDICATOR_SUPPORT_RESISTANCE, _('Support/Resistance Levels')),
    ]

    name = models.CharField(
        max_length=50,
        choices=INDICATOR_CHOICES,
        unique=True,
        verbose_name=_('Name')
    )
    display_name = models.CharField(
        max_length=100,
        verbose_name=_('Display Name')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    default_params = models.JSONField(
        default=dict,
        verbose_name=_('Default Parameters'),
        help_text=_('Default calculation parameters')
    )
    output_fields = models.JSONField(
        default=list,
        verbose_name=_('Output Fields'),
        help_text=_('List of output field names')
    )

    class Meta:
        db_table = 'indicators_indicator_type'
        verbose_name = _('Indicator Type')
        verbose_name_plural = _('Indicator Types')
        ordering = ['name']

    def __str__(self):
        return self.display_name


class IndicatorConfig(BaseModel):
    """
    Configuration for indicator calculations.

    Defines how an indicator should be calculated for a specific
    trading pair and timeframe.
    """
    indicator_type = models.ForeignKey(
        IndicatorType,
        on_delete=models.CASCADE,
        related_name='configs',
        verbose_name=_('Indicator Type')
    )
    trading_pair = models.ForeignKey(
        TradingPair,
        on_delete=models.CASCADE,
        related_name='indicator_configs',
        verbose_name=_('Trading Pair')
    )
    timeframe = models.CharField(
        max_length=10,
        verbose_name=_('Timeframe')
    )
    params = models.JSONField(
        default=dict,
        verbose_name=_('Parameters'),
        help_text=_('Custom parameters (overrides defaults)')
    )
    is_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Is Enabled')
    )

    class Meta:
        db_table = 'indicators_config'
        verbose_name = _('Indicator Configuration')
        verbose_name_plural = _('Indicator Configurations')
        unique_together = ['indicator_type', 'trading_pair', 'timeframe']

    def __str__(self):
        return f"{self.indicator_type.name} - {self.trading_pair.symbol} {self.timeframe}"

    def get_params(self) -> dict:
        """Get merged parameters (custom over defaults)."""
        params = self.indicator_type.default_params.copy()
        params.update(self.params)
        return params


class IndicatorResult(BaseModel):
    """
    Calculated indicator values.

    Stores the output of indicator calculations, with flexible
    JSON storage for different indicator types.
    """
    config = models.ForeignKey(
        IndicatorConfig,
        on_delete=models.CASCADE,
        related_name='results',
        verbose_name=_('Configuration')
    )
    ohlcv = models.ForeignKey(
        OHLCV,
        on_delete=models.CASCADE,
        related_name='indicator_results',
        verbose_name=_('OHLCV')
    )
    timestamp = models.DateTimeField(
        verbose_name=_('Timestamp')
    )
    values = models.JSONField(
        verbose_name=_('Values'),
        help_text=_('''
            Indicator output values. Examples:
            - RSI: {"rsi": 55.2}
            - MACD: {"macd_line": 0.0012, "signal_line": 0.0008, "histogram": 0.0004}
            - ADX: {"adx": 28, "plus_di": 22, "minus_di": 18}
            - Stochastic: {"k": 52, "d": 48}
            - Bollinger: {"upper": 1.0900, "middle": 1.0850, "lower": 1.0800}
        ''')
    )

    class Meta:
        db_table = 'indicators_result'
        verbose_name = _('Indicator Result')
        verbose_name_plural = _('Indicator Results')
        unique_together = ['config', 'timestamp']
        indexes = [
            models.Index(fields=['config', 'timestamp']),
            models.Index(fields=['config', '-timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.config} @ {self.timestamp}"

    def get_value(self, field_name: str, default=None):
        """Get a specific value from the results."""
        return self.values.get(field_name, default)
