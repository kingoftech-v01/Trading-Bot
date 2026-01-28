"""
Tests for combinations app services.
"""

from django.test import TestCase
from unittest.mock import Mock, patch
from decimal import Decimal

from apps.combinations.services import (
    CombinationEvaluator,
    GoldenConfluence,
    MeanReversion,
    BreakoutMomentum,
    HarmonicConfluence,
    LinearRegressionChannel,
    MultiTimeframe,
    StochasticCrossover,
    UltimateConfluence,
)


class BaseCombinationTestMixin:
    """Mixin for testing combination services."""

    def get_mock_indicators_bullish(self):
        """Get mock indicators for bullish scenario."""
        return {
            'current_close': 100.0,
            'rsi': {
                'rsi': 55,
                'is_bullish': True,
                'is_oversold': False,
                'is_overbought': False,
            },
            'macd': {
                'macd_line': 0.5,
                'signal_line': 0.3,
                'histogram': 0.2,
                'is_bullish': True,
                'histogram_positive': True,
                'histogram_growing': True,
            },
            'adx': {
                'adx': 30,
                'plus_di': 25,
                'minus_di': 15,
                'is_trending': True,
                'is_bullish_trend': True,
                'is_bearish_trend': False,
            },
            'stochastic': {
                'k': 60,
                'd': 50,
                'previous_k': 45,
                'k_above_d': True,
                'is_oversold': False,
                'is_overbought': False,
            },
            'stochastic_slow': {
                'k': 55,
                'd': 45,
                'previous_k': 40,
            },
            'bollinger': {
                'upper': 105,
                'middle': 100,
                'lower': 95,
                'width': 10,
                'price_above_middle': True,
                'price_near_lower': False,
                'price_near_upper': False,
            },
            'linear_regression': {
                'slope': 0.05,
                'r_squared': 0.75,
                'predicted': 101,
                'upper_channel': 103,
                'lower_channel': 97,
                'is_uptrend': True,
                'is_downtrend': False,
                'is_clear_trend': True,
                'price_at_lower_channel': True,
            },
            'cci': {
                'cci': 50,
                'is_positive': True,
                'is_rising': True,
            },
            'atr': {
                'atr': 2.5,
                'atr_percent': 2.5,
            },
            'volume_profile': {
                'volume_ratio': 1.5,
                'is_above_average': True,
            },
            'support_resistance': {
                'nearest_support': 95,
                'nearest_resistance': 110,
                'price_above_support': True,
            },
        }

    def get_mock_indicators_bearish(self):
        """Get mock indicators for bearish scenario."""
        return {
            'current_close': 100.0,
            'rsi': {
                'rsi': 45,
                'is_bullish': False,
                'is_oversold': False,
                'is_overbought': False,
            },
            'macd': {
                'macd_line': -0.5,
                'signal_line': -0.3,
                'histogram': -0.2,
                'is_bullish': False,
                'histogram_positive': False,
                'histogram_growing': False,
            },
            'adx': {
                'adx': 30,
                'plus_di': 15,
                'minus_di': 25,
                'is_trending': True,
                'is_bullish_trend': False,
                'is_bearish_trend': True,
            },
            'stochastic': {
                'k': 40,
                'd': 50,
                'previous_k': 55,
                'k_above_d': False,
                'is_oversold': False,
                'is_overbought': False,
            },
            'stochastic_slow': {
                'k': 45,
                'd': 55,
                'previous_k': 60,
            },
            'bollinger': {
                'upper': 105,
                'middle': 100,
                'lower': 95,
                'width': 10,
                'price_above_middle': False,
                'price_near_lower': False,
                'price_near_upper': True,
            },
            'linear_regression': {
                'slope': -0.05,
                'r_squared': 0.75,
                'predicted': 99,
                'upper_channel': 103,
                'lower_channel': 97,
                'is_uptrend': False,
                'is_downtrend': True,
                'is_clear_trend': True,
                'price_at_upper_channel': True,
            },
            'cci': {
                'cci': -50,
                'is_positive': False,
                'is_rising': False,
            },
            'atr': {
                'atr': 2.5,
                'atr_percent': 2.5,
            },
            'volume_profile': {
                'volume_ratio': 1.5,
                'is_above_average': True,
            },
            'support_resistance': {
                'nearest_support': 90,
                'nearest_resistance': 105,
                'price_above_support': True,
            },
        }


class GoldenConfluenceTest(TestCase, BaseCombinationTestMixin):
    """Tests for GoldenConfluence combination."""

    def setUp(self):
        self.combo = GoldenConfluence()

    def test_get_name(self):
        self.assertEqual(self.combo.get_name(), 'golden_confluence')

    def test_get_display_name(self):
        self.assertEqual(self.combo.get_display_name(), 'Golden Confluence')

    def test_get_win_rate(self):
        self.assertEqual(self.combo.get_win_rate(), 62.0)

    def test_get_risk_reward_ratio(self):
        self.assertEqual(self.combo.get_risk_reward_ratio(), 3.8)

    def test_get_required_indicators(self):
        indicators = self.combo.get_required_indicators()
        self.assertIn('rsi', indicators)
        self.assertIn('macd', indicators)
        self.assertIn('adx', indicators)

    def test_evaluate_buy_bullish(self):
        indicators = self.get_mock_indicators_bullish()
        is_met, confidence, criteria = self.combo.evaluate_buy(indicators)
        self.assertIsInstance(is_met, bool)
        self.assertIsInstance(confidence, int)
        self.assertIsInstance(criteria, dict)

    def test_evaluate_sell_bearish(self):
        indicators = self.get_mock_indicators_bearish()
        is_met, confidence, criteria = self.combo.evaluate_sell(indicators)
        self.assertIsInstance(is_met, bool)
        self.assertIsInstance(confidence, int)
        self.assertIsInstance(criteria, dict)


class MeanReversionTest(TestCase, BaseCombinationTestMixin):
    """Tests for MeanReversion combination."""

    def setUp(self):
        self.combo = MeanReversion()

    def test_get_name(self):
        self.assertEqual(self.combo.get_name(), 'mean_reversion')

    def test_get_win_rate(self):
        self.assertEqual(self.combo.get_win_rate(), 68.0)

    def test_get_risk_reward_ratio(self):
        self.assertEqual(self.combo.get_risk_reward_ratio(), 3.2)


class BreakoutMomentumTest(TestCase, BaseCombinationTestMixin):
    """Tests for BreakoutMomentum combination."""

    def setUp(self):
        self.combo = BreakoutMomentum()

    def test_get_name(self):
        self.assertEqual(self.combo.get_name(), 'breakout_momentum')

    def test_get_win_rate(self):
        self.assertEqual(self.combo.get_win_rate(), 56.0)

    def test_get_risk_reward_ratio(self):
        self.assertEqual(self.combo.get_risk_reward_ratio(), 4.1)


class HarmonicConfluenceTest(TestCase, BaseCombinationTestMixin):
    """Tests for HarmonicConfluence combination."""

    def setUp(self):
        self.combo = HarmonicConfluence()

    def test_get_name(self):
        self.assertEqual(self.combo.get_name(), 'harmonic_confluence')

    def test_get_win_rate(self):
        self.assertEqual(self.combo.get_win_rate(), 64.0)


class LinearRegressionChannelTest(TestCase, BaseCombinationTestMixin):
    """Tests for LinearRegressionChannel combination."""

    def setUp(self):
        self.combo = LinearRegressionChannel()

    def test_get_name(self):
        self.assertEqual(self.combo.get_name(), 'linear_regression_channel')

    def test_get_win_rate(self):
        self.assertEqual(self.combo.get_win_rate(), 59.0)


class MultiTimeframeTest(TestCase, BaseCombinationTestMixin):
    """Tests for MultiTimeframe combination."""

    def setUp(self):
        self.combo = MultiTimeframe()

    def test_get_name(self):
        self.assertEqual(self.combo.get_name(), 'multi_timeframe')

    def test_get_win_rate(self):
        self.assertEqual(self.combo.get_win_rate(), 66.0)


class StochasticCrossoverTest(TestCase, BaseCombinationTestMixin):
    """Tests for StochasticCrossover combination."""

    def setUp(self):
        self.combo = StochasticCrossover()

    def test_get_name(self):
        self.assertEqual(self.combo.get_name(), 'stochastic_crossover')

    def test_get_win_rate(self):
        self.assertEqual(self.combo.get_win_rate(), 71.0)


class UltimateConfluenceTest(TestCase, BaseCombinationTestMixin):
    """Tests for UltimateConfluence combination."""

    def setUp(self):
        self.combo = UltimateConfluence()

    def test_get_name(self):
        self.assertEqual(self.combo.get_name(), 'ultimate_confluence')

    def test_get_win_rate(self):
        self.assertEqual(self.combo.get_win_rate(), 58.0)

    def test_get_risk_reward_ratio(self):
        self.assertEqual(self.combo.get_risk_reward_ratio(), 4.5)


class CombinationEvaluatorTest(TestCase):
    """Tests for CombinationEvaluator service."""

    def setUp(self):
        self.evaluator = CombinationEvaluator()

    def test_initialization(self):
        """Test evaluator initializes with 8 combinations."""
        self.assertEqual(len(self.evaluator.combinations), 8)

    def test_get_combination_info(self):
        """Test getting combination info."""
        info = self.evaluator.get_combination_info()
        self.assertEqual(len(info), 8)
        for combo_info in info:
            self.assertIn('name', combo_info)
            self.assertIn('display_name', combo_info)
            self.assertIn('win_rate', combo_info)
            self.assertIn('risk_reward', combo_info)

    def test_evaluate_single_valid(self):
        """Test evaluating a single valid combination."""
        ohlcv_data = self._generate_mock_ohlcv()
        result = self.evaluator.evaluate_single('golden_confluence', ohlcv_data)
        self.assertIsNotNone(result)
        self.assertIn('signal', result)
        self.assertIn('confidence', result)

    def test_evaluate_single_invalid(self):
        """Test evaluating an invalid combination."""
        ohlcv_data = self._generate_mock_ohlcv()
        result = self.evaluator.evaluate_single('invalid_combo', ohlcv_data)
        self.assertIsNone(result)

    def test_evaluate_all(self):
        """Test evaluating all combinations."""
        ohlcv_data = self._generate_mock_ohlcv()
        results = self.evaluator.evaluate_all(ohlcv_data)

        self.assertIn('buy_votes', results)
        self.assertIn('sell_votes', results)
        self.assertIn('neutral_votes', results)
        self.assertIn('summary', results)
        self.assertIn('details', results)

        # Check summary
        summary = results['summary']
        self.assertEqual(summary['total_combinations'], 8)
        total_votes = (
            summary['buy_count'] +
            summary['sell_count'] +
            summary['neutral_count']
        )
        self.assertEqual(total_votes, 8)

    def _generate_mock_ohlcv(self, count=100):
        """Generate mock OHLCV data."""
        from datetime import datetime, timedelta
        data = []
        base_price = 100.0
        base_time = datetime.now() - timedelta(hours=count)

        for i in range(count):
            open_price = base_price + (i * 0.1)
            high = open_price + 1.0
            low = open_price - 1.0
            close = open_price + 0.5
            volume = 1000 + (i * 10)

            data.append({
                'timestamp': base_time + timedelta(hours=i),
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume,
            })

        return data
