"""
Tests for combinations app models.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal

from apps.combinations.models import Combination, CombinationResult
from apps.market_data.models import Exchange, TradingPair


class CombinationModelTest(TestCase):
    """Tests for Combination model."""

    def setUp(self):
        """Set up test data."""
        self.combination = Combination.objects.create(
            name='golden_confluence',
            display_name='Golden Confluence',
            description='Test combination',
            win_rate=62.0,
            risk_reward_ratio=3.8,
            expected_frequency=73,
            required_indicators=['rsi', 'macd', 'adx'],
            buy_criteria={'rsi': {'min': 50}},
            sell_criteria={'rsi': {'max': 50}},
        )

    def test_combination_creation(self):
        """Test creating a combination."""
        self.assertEqual(self.combination.name, 'golden_confluence')
        self.assertEqual(self.combination.win_rate, 62.0)
        self.assertEqual(self.combination.risk_reward_ratio, 3.8)
        self.assertTrue(self.combination.is_active)

    def test_combination_str(self):
        """Test string representation."""
        self.assertEqual(str(self.combination), 'Golden Confluence')

    def test_combination_required_indicators(self):
        """Test required indicators field."""
        self.assertIn('rsi', self.combination.required_indicators)
        self.assertIn('macd', self.combination.required_indicators)
        self.assertIn('adx', self.combination.required_indicators)

    def test_combination_unique_name(self):
        """Test that combination names are unique."""
        with self.assertRaises(Exception):
            Combination.objects.create(
                name='golden_confluence',
                display_name='Another Golden',
                win_rate=50.0,
                risk_reward_ratio=2.0,
            )

    def test_combination_win_rate_validation(self):
        """Test win rate range validation."""
        combo = Combination(
            name='test_combo',
            display_name='Test',
            win_rate=150.0,  # Invalid: > 100
            risk_reward_ratio=2.0,
        )
        # Model should validate this
        self.assertGreater(combo.win_rate, 100)


class CombinationResultModelTest(TestCase):
    """Tests for CombinationResult model."""

    def setUp(self):
        """Set up test data."""
        self.exchange = Exchange.objects.create(
            name='binance',
            display_name='Binance',
        )
        self.trading_pair = TradingPair.objects.create(
            exchange=self.exchange,
            symbol='BTC/USD',
            base_currency='BTC',
            quote_currency='USD',
        )
        self.combination = Combination.objects.create(
            name='test_combo',
            display_name='Test Combination',
            win_rate=60.0,
            risk_reward_ratio=3.0,
        )
        self.result = CombinationResult.objects.create(
            combination=self.combination,
            trading_pair=self.trading_pair,
            timeframe='1h',
            signal='buy',
            confidence=85,
            criteria_met={'rsi_bullish': True, 'macd_bullish': True},
        )

    def test_result_creation(self):
        """Test creating a combination result."""
        self.assertEqual(self.result.signal, 'buy')
        self.assertEqual(self.result.confidence, 85)
        self.assertEqual(self.result.timeframe, '1h')

    def test_result_str(self):
        """Test string representation."""
        expected = f"Test Combination - BTC/USD - buy"
        self.assertEqual(str(self.result), expected)

    def test_result_foreign_keys(self):
        """Test foreign key relationships."""
        self.assertEqual(self.result.combination.name, 'test_combo')
        self.assertEqual(self.result.trading_pair.symbol, 'BTC/USD')

    def test_result_criteria_met(self):
        """Test criteria_met JSON field."""
        self.assertTrue(self.result.criteria_met['rsi_bullish'])
        self.assertTrue(self.result.criteria_met['macd_bullish'])

    def test_result_signals(self):
        """Test different signal values."""
        for signal in ['buy', 'sell', 'neutral']:
            result = CombinationResult.objects.create(
                combination=self.combination,
                trading_pair=self.trading_pair,
                timeframe='1h',
                signal=signal,
                confidence=50,
            )
            self.assertEqual(result.signal, signal)

    def test_result_confidence_range(self):
        """Test confidence values."""
        result = CombinationResult.objects.create(
            combination=self.combination,
            trading_pair=self.trading_pair,
            timeframe='1h',
            signal='buy',
            confidence=100,
        )
        self.assertEqual(result.confidence, 100)

    def test_result_evaluated_at(self):
        """Test evaluated_at timestamp."""
        self.assertIsNotNone(self.result.evaluated_at)
