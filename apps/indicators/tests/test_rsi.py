"""
Tests for RSI Indicator.
"""

from django.test import TestCase
from datetime import datetime, timedelta
from apps.indicators.services.rsi import RSIIndicator


class RSIIndicatorTestCase(TestCase):
    """Test cases for RSI indicator."""

    def setUp(self):
        self.indicator = RSIIndicator()
        # Generate sample OHLCV data
        self.ohlcv_data = []
        base_price = 100.0
        for i in range(50):
            price = base_price + (i * 0.1) + ((-1) ** i * 0.5)
            self.ohlcv_data.append({
                'timestamp': datetime.now() + timedelta(hours=i),
                'open': price - 0.1,
                'high': price + 0.2,
                'low': price - 0.2,
                'close': price,
                'volume': 1000,
            })

    def test_default_params(self):
        """Test default parameters."""
        params = self.indicator.default_params()
        self.assertEqual(params['period'], 14)
        self.assertEqual(params['overbought'], 70)
        self.assertEqual(params['oversold'], 30)

    def test_calculate_returns_values(self):
        """Test RSI calculation returns expected keys."""
        result = self.indicator.calculate(self.ohlcv_data)
        self.assertIn('rsi', result)
        self.assertIn('previous_rsi', result)
        self.assertIn('is_overbought', result)
        self.assertIn('is_oversold', result)

    def test_rsi_range(self):
        """Test RSI value is between 0 and 100."""
        result = self.indicator.calculate(self.ohlcv_data)
        if result['rsi'] is not None:
            self.assertGreaterEqual(result['rsi'], 0)
            self.assertLessEqual(result['rsi'], 100)

    def test_insufficient_data(self):
        """Test with insufficient data."""
        short_data = self.ohlcv_data[:5]
        result = self.indicator.calculate(short_data)
        self.assertIsNone(result['rsi'])
