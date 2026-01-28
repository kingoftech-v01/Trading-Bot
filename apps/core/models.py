"""
Core Models - Base classes for all models in the trading bot.

This module provides abstract base models with common fields:
- UUID primary key
- Timestamps (created_at, updated_at)
- Soft delete (is_active)
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    """
    Abstract base model with UUID primary key and timestamps.

    All models in the trading bot should inherit from this class
    to ensure consistent ID generation and timestamp tracking.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def soft_delete(self):
        """Soft delete the object by setting is_active to False."""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

    def restore(self):
        """Restore a soft-deleted object."""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])


class TimeframeMixin(models.Model):
    """
    Mixin for models that work with different timeframes.

    Provides a standardized timeframe field with predefined choices.
    """
    TIMEFRAME_15M = '15m'
    TIMEFRAME_1H = '1h'
    TIMEFRAME_4H = '4h'
    TIMEFRAME_1D = '1d'

    TIMEFRAME_CHOICES = [
        (TIMEFRAME_15M, _('15 Minutes')),
        (TIMEFRAME_1H, _('1 Hour')),
        (TIMEFRAME_4H, _('4 Hours')),
        (TIMEFRAME_1D, _('1 Day')),
    ]

    timeframe = models.CharField(
        max_length=10,
        choices=TIMEFRAME_CHOICES,
        default=TIMEFRAME_1H,
        verbose_name=_('Timeframe')
    )

    class Meta:
        abstract = True

    @property
    def timeframe_minutes(self) -> int:
        """Return the timeframe in minutes."""
        mapping = {
            self.TIMEFRAME_15M: 15,
            self.TIMEFRAME_1H: 60,
            self.TIMEFRAME_4H: 240,
            self.TIMEFRAME_1D: 1440,
        }
        return mapping.get(self.timeframe, 60)


class SignalDirectionMixin(models.Model):
    """
    Mixin for models that represent trading signals.

    Provides standardized signal direction choices.
    """
    SIGNAL_BUY = 'buy'
    SIGNAL_SELL = 'sell'
    SIGNAL_NEUTRAL = 'neutral'
    SIGNAL_WAIT = 'wait'

    SIGNAL_CHOICES = [
        (SIGNAL_BUY, _('Buy')),
        (SIGNAL_SELL, _('Sell')),
        (SIGNAL_NEUTRAL, _('Neutral')),
        (SIGNAL_WAIT, _('Wait')),
    ]

    signal = models.CharField(
        max_length=10,
        choices=SIGNAL_CHOICES,
        default=SIGNAL_NEUTRAL,
        verbose_name=_('Signal')
    )

    class Meta:
        abstract = True

    @property
    def is_actionable(self) -> bool:
        """Return True if the signal is actionable (buy or sell)."""
        return self.signal in [self.SIGNAL_BUY, self.SIGNAL_SELL]


class StatusMixin(models.Model):
    """
    Mixin for models that have a status workflow.
    """
    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_ACTIVE, _('Active')),
        (STATUS_COMPLETED, _('Completed')),
        (STATUS_CANCELLED, _('Cancelled')),
        (STATUS_FAILED, _('Failed')),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name=_('Status')
    )

    class Meta:
        abstract = True
