"""
Tests for Market Data Models.

Tests Exchange, TradingPair, OHLCV, and CorrelationMatrix models.
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from apps.market_data.models import Exchange, TradingPair, OHLCV, CorrelationMatrix


class ExchangeModelTestCase(TestCase):
    """Test cases for Exchange model."""

    def test_create_exchange(self):
        """Test creating an exchange."""
        exchange = Exchange.objects.create(
            name='TestExchange',
            api_type=Exchange.API_TYPE_REST,
            base_url='https://api.test.com',
            is_enabled=True
        )
        self.assertEqual(exchange.name, 'TestExchange')
        self.assertEqual(exchange.api_type, 'rest')
        self.assertTrue(exchange.is_enabled)

    def test_exchange_str(self):
        """Test exchange string representation."""
        exchange = Exchange.objects.create(name='Binance')
        self.assertEqual(str(exchange), 'Binance')


class TradingPairModelTestCase(TestCase):
    """Test cases for TradingPair model."""

    def setUp(self):
        self.exchange = Exchange.objects.create(
            name='TestExchange',
            api_type=Exchange.API_TYPE_REST
        )

    def test_create_trading_pair(self):
        """Test creating a trading pair."""
        pair = TradingPair.objects.create(
            symbol='EURUSD',
            base_currency='EUR',
            quote_currency='USD',
            exchange=self.exchange,
            pip_value=Decimal('0.0001'),
            is_forex=True
        )
        self.assertEqual(pair.symbol, 'EURUSD')
        self.assertTrue(pair.is_forex)

    def test_display_symbol(self):
        """Test display_symbol property."""
        pair = TradingPair.objects.create(
            symbol='EURUSD',
            base_currency='EUR',
            quote_currency='USD',
            exchange=self.exchange
        )
        self.assertEqual(pair.display_symbol, 'EUR/USD')


class OHLCVModelTestCase(TestCase):
    """Test cases for OHLCV model."""

    def setUp(self):
        self.exchange = Exchange.objects.create(name='TestExchange')
        self.pair = TradingPair.objects.create(
            symbol='EURUSD',
            base_currency='EUR',
            quote_currency='USD',
            exchange=self.exchange
        )

    def test_create_ohlcv(self):
        """Test creating OHLCV record."""
        ohlcv = OHLCV.objects.create(
            trading_pair=self.pair,
            timeframe='1h',
            timestamp=timezone.now(),
            open=Decimal('1.0850'),
            high=Decimal('1.0900'),
            low=Decimal('1.0800'),
            close=Decimal('1.0875'),
            volume=Decimal('1000')
        )
        self.assertEqual(ohlcv.trading_pair, self.pair)
        self.assertEqual(ohlcv.timeframe, '1h')

    def test_is_bullish(self):
        """Test is_bullish property."""
        ohlcv = OHLCV.objects.create(
            trading_pair=self.pair,
            timeframe='1h',
            timestamp=timezone.now(),
            open=Decimal('1.0850'),
            high=Decimal('1.0900'),
            low=Decimal('1.0800'),
            close=Decimal('1.0875'),  # close > open
            volume=Decimal('1000')
        )
        self.assertTrue(ohlcv.is_bullish)
        self.assertFalse(ohlcv.is_bearish)

    def test_is_bearish(self):
        """Test is_bearish property."""
        ohlcv = OHLCV.objects.create(
            trading_pair=self.pair,
            timeframe='1h',
            timestamp=timezone.now(),
            open=Decimal('1.0875'),
            high=Decimal('1.0900'),
            low=Decimal('1.0800'),
            close=Decimal('1.0850'),  # close < open
            volume=Decimal('1000')
        )
        self.assertTrue(ohlcv.is_bearish)
        self.assertFalse(ohlcv.is_bullish)

    def test_range_property(self):
        """Test range property."""
        ohlcv = OHLCV.objects.create(
            trading_pair=self.pair,
            timeframe='1h',
            timestamp=timezone.now(),
            open=Decimal('1.0850'),
            high=Decimal('1.0900'),
            low=Decimal('1.0800'),
            close=Decimal('1.0875'),
            volume=Decimal('1000')
        )
        self.assertEqual(ohlcv.range, Decimal('0.0100'))  # 1.0900 - 1.0800


class CorrelationMatrixModelTestCase(TestCase):
    """Test cases for CorrelationMatrix model."""

    def setUp(self):
        self.exchange = Exchange.objects.create(name='TestExchange')
        self.pair1 = TradingPair.objects.create(
            symbol='EURUSD',
            base_currency='EUR',
            quote_currency='USD',
            exchange=self.exchange
        )
        self.pair2 = TradingPair.objects.create(
            symbol='GBPUSD',
            base_currency='GBP',
            quote_currency='USD',
            exchange=self.exchange
        )

    def test_is_strong_positive(self):
        """Test is_strong_positive property."""
        correlation = CorrelationMatrix.objects.create(
            primary_pair=self.pair1,
            secondary_pair=self.pair2,
            timeframe='1h',
            correlation_value=Decimal('0.85'),
            calculation_date=timezone.now().date()
        )
        self.assertTrue(correlation.is_strong_positive)
        self.assertFalse(correlation.is_strong_negative)

    def test_is_strong_negative(self):
        """Test is_strong_negative property."""
        correlation = CorrelationMatrix.objects.create(
            primary_pair=self.pair1,
            secondary_pair=self.pair2,
            timeframe='1h',
            correlation_value=Decimal('-0.85'),
            calculation_date=timezone.now().date()
        )
        self.assertTrue(correlation.is_strong_negative)
        self.assertFalse(correlation.is_strong_positive)
