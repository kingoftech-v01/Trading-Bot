"""
Tests for Core Models.

Tests the BaseModel and mixin functionality.
"""

import uuid
from django.test import TestCase
from django.db import models
from django.utils import timezone
from apps.core.models import BaseModel, TimeframeMixin, SignalDirectionMixin


class ConcreteModel(BaseModel):
    """Concrete model for testing BaseModel."""
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'core'


class TimeframeModel(BaseModel, TimeframeMixin):
    """Concrete model for testing TimeframeMixin."""

    class Meta:
        app_label = 'core'


class SignalModel(BaseModel, SignalDirectionMixin):
    """Concrete model for testing SignalDirectionMixin."""

    class Meta:
        app_label = 'core'


class BaseModelTestCase(TestCase):
    """Test cases for BaseModel."""

    def test_uuid_primary_key(self):
        """Test that BaseModel has UUID primary key."""
        # Check that the id field is defined as UUIDField
        id_field = BaseModel._meta.get_field('id')
        self.assertIsInstance(id_field, models.UUIDField)
        self.assertTrue(id_field.primary_key)
        self.assertFalse(id_field.editable)

    def test_uuid_is_valid_format(self):
        """Test that generated UUID is valid."""
        test_uuid = uuid.uuid4()
        self.assertIsInstance(test_uuid, uuid.UUID)
        self.assertEqual(len(str(test_uuid)), 36)

    def test_timestamps_fields_exist(self):
        """Test that created_at and updated_at fields exist."""
        created_at_field = BaseModel._meta.get_field('created_at')
        updated_at_field = BaseModel._meta.get_field('updated_at')

        self.assertIsInstance(created_at_field, models.DateTimeField)
        self.assertIsInstance(updated_at_field, models.DateTimeField)
        self.assertTrue(created_at_field.auto_now_add)
        self.assertTrue(updated_at_field.auto_now)

    def test_is_active_default_true(self):
        """Test that is_active defaults to True."""
        is_active_field = BaseModel._meta.get_field('is_active')
        self.assertIsInstance(is_active_field, models.BooleanField)
        self.assertTrue(is_active_field.default)

    def test_soft_delete_method_exists(self):
        """Test that soft_delete method exists."""
        self.assertTrue(hasattr(BaseModel, 'soft_delete'))
        self.assertTrue(callable(getattr(BaseModel, 'soft_delete')))

    def test_restore_method_exists(self):
        """Test that restore method exists."""
        self.assertTrue(hasattr(BaseModel, 'restore'))
        self.assertTrue(callable(getattr(BaseModel, 'restore')))

    def test_model_is_abstract(self):
        """Test that BaseModel is abstract."""
        self.assertTrue(BaseModel._meta.abstract)

    def test_default_ordering(self):
        """Test that default ordering is by -created_at."""
        self.assertEqual(BaseModel._meta.ordering, ['-created_at'])


class TimeframeMixinTestCase(TestCase):
    """Test cases for TimeframeMixin."""

    def test_timeframe_choices_defined(self):
        """Test that timeframe choices are defined."""
        expected_choices = [
            ('15m', '15 Minutes'),
            ('1h', '1 Hour'),
            ('4h', '4 Hours'),
            ('1d', '1 Day'),
        ]
        self.assertEqual(len(TimeframeMixin.TIMEFRAME_CHOICES), 4)

    def test_timeframe_minutes_15m(self):
        """Test 15m timeframe returns 15 minutes."""
        model = TimeframeModel()
        model.timeframe = '15m'
        self.assertEqual(model.timeframe_minutes, 15)

    def test_timeframe_minutes_1h(self):
        """Test 1h timeframe returns 60 minutes."""
        model = TimeframeModel()
        model.timeframe = '1h'
        self.assertEqual(model.timeframe_minutes, 60)

    def test_timeframe_minutes_4h(self):
        """Test 4h timeframe returns 240 minutes."""
        model = TimeframeModel()
        model.timeframe = '4h'
        self.assertEqual(model.timeframe_minutes, 240)

    def test_timeframe_minutes_1d(self):
        """Test 1d timeframe returns 1440 minutes."""
        model = TimeframeModel()
        model.timeframe = '1d'
        self.assertEqual(model.timeframe_minutes, 1440)

    def test_default_timeframe_is_1h(self):
        """Test that default timeframe is 1h."""
        timeframe_field = TimeframeMixin._meta.get_field('timeframe')
        self.assertEqual(timeframe_field.default, '1h')

    def test_timeframe_minutes_unknown_returns_default(self):
        """Test that unknown timeframe returns default (60)."""
        model = TimeframeModel()
        model.timeframe = 'unknown'
        self.assertEqual(model.timeframe_minutes, 60)


class SignalDirectionMixinTestCase(TestCase):
    """Test cases for SignalDirectionMixin."""

    def test_signal_choices_defined(self):
        """Test that signal choices are defined."""
        self.assertEqual(len(SignalDirectionMixin.SIGNAL_CHOICES), 4)

    def test_signal_constants(self):
        """Test signal constant values."""
        self.assertEqual(SignalDirectionMixin.SIGNAL_BUY, 'buy')
        self.assertEqual(SignalDirectionMixin.SIGNAL_SELL, 'sell')
        self.assertEqual(SignalDirectionMixin.SIGNAL_NEUTRAL, 'neutral')
        self.assertEqual(SignalDirectionMixin.SIGNAL_WAIT, 'wait')

    def test_is_actionable_buy(self):
        """Test that buy signal is actionable."""
        model = SignalModel()
        model.signal = 'buy'
        self.assertTrue(model.is_actionable)

    def test_is_actionable_sell(self):
        """Test that sell signal is actionable."""
        model = SignalModel()
        model.signal = 'sell'
        self.assertTrue(model.is_actionable)

    def test_is_not_actionable_neutral(self):
        """Test that neutral signal is not actionable."""
        model = SignalModel()
        model.signal = 'neutral'
        self.assertFalse(model.is_actionable)

    def test_is_not_actionable_wait(self):
        """Test that wait signal is not actionable."""
        model = SignalModel()
        model.signal = 'wait'
        self.assertFalse(model.is_actionable)

    def test_default_signal_is_neutral(self):
        """Test that default signal is neutral."""
        signal_field = SignalDirectionMixin._meta.get_field('signal')
        self.assertEqual(signal_field.default, 'neutral')
