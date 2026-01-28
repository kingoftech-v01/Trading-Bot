"""
Tests for signals app services.
"""

from django.test import TestCase
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from apps.signals.services import (
    VotingSystem,
    SignalGenerator,
    ConfluenceScorer,
    MultiPairValidator,
)
from apps.signals.services.voting_system import VoteResult, VotingResult
from apps.market_data.models import Exchange, TradingPair


class VotingSystemTest(TestCase):
    """Tests for VotingSystem service."""

    def setUp(self):
        self.voting_system = VotingSystem(voting_threshold=5)

    def test_initialization(self):
        """Test voting system initialization."""
        self.assertEqual(self.voting_system.voting_threshold, 5)

    def test_collect_votes(self):
        """Test collecting votes from combinations."""
        ohlcv_data = self._generate_mock_ohlcv()
        result = self.voting_system.collect_votes(ohlcv_data)

        self.assertIsInstance(result, VotingResult)
        self.assertIn(result.final_signal, ['buy', 'sell', 'wait'])
        self.assertIsInstance(result.buy_votes, list)
        self.assertIsInstance(result.sell_votes, list)
        self.assertIsInstance(result.neutral_votes, list)

    def test_determine_signal_buy(self):
        """Test determining buy signal."""
        buy_votes = [
            VoteResult('combo1', 'Combo 1', 'buy', 80, 60.0, 3.0, {}),
            VoteResult('combo2', 'Combo 2', 'buy', 75, 65.0, 3.5, {}),
            VoteResult('combo3', 'Combo 3', 'buy', 85, 62.0, 3.2, {}),
            VoteResult('combo4', 'Combo 4', 'buy', 70, 58.0, 4.0, {}),
            VoteResult('combo5', 'Combo 5', 'buy', 90, 71.0, 3.0, {}),
        ]
        sell_votes = [
            VoteResult('combo6', 'Combo 6', 'sell', 60, 56.0, 4.1, {}),
        ]

        signal, count, threshold_met = self.voting_system._determine_signal(
            buy_votes, sell_votes
        )

        self.assertEqual(signal, 'buy')
        self.assertEqual(count, 5)
        self.assertTrue(threshold_met)

    def test_determine_signal_wait(self):
        """Test determining wait signal when threshold not met."""
        buy_votes = [
            VoteResult('combo1', 'Combo 1', 'buy', 80, 60.0, 3.0, {}),
            VoteResult('combo2', 'Combo 2', 'buy', 75, 65.0, 3.5, {}),
        ]
        sell_votes = [
            VoteResult('combo3', 'Combo 3', 'sell', 60, 56.0, 4.1, {}),
        ]

        signal, count, threshold_met = self.voting_system._determine_signal(
            buy_votes, sell_votes
        )

        self.assertEqual(signal, 'wait')
        self.assertFalse(threshold_met)

    def test_calculate_confluence_score(self):
        """Test confluence score calculation."""
        votes = [
            VoteResult('combo1', 'Combo 1', 'buy', 80, 60.0, 3.0, {}),
            VoteResult('combo2', 'Combo 2', 'buy', 75, 65.0, 3.5, {}),
            VoteResult('combo3', 'Combo 3', 'buy', 85, 62.0, 3.2, {}),
            VoteResult('combo4', 'Combo 4', 'buy', 70, 58.0, 4.0, {}),
            VoteResult('combo5', 'Combo 5', 'buy', 90, 71.0, 3.0, {}),
        ]

        score = self.voting_system._calculate_confluence_score(votes)

        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)

    def test_validate_signal_strength(self):
        """Test signal strength validation."""
        voting_result = VotingResult(
            final_signal='buy',
            buy_votes=[VoteResult('c', 'C', 'buy', 80, 60, 3.0, {})] * 5,
            sell_votes=[],
            neutral_votes=[],
            vote_count=5,
            threshold_met=True,
            confluence_score=75.0,
            average_confidence=80.0,
        )

        is_valid, reason = self.voting_system.validate_signal_strength(
            voting_result,
            min_confluence=50.0,
            min_confidence=60.0
        )

        self.assertTrue(is_valid)
        self.assertEqual(reason, "Signal validated")

    def _generate_mock_ohlcv(self, count=100):
        """Generate mock OHLCV data."""
        data = []
        base_price = 100.0
        base_time = datetime.now() - timedelta(hours=count)

        for i in range(count):
            data.append({
                'timestamp': base_time + timedelta(hours=i),
                'open': base_price + (i * 0.1),
                'high': base_price + (i * 0.1) + 1.0,
                'low': base_price + (i * 0.1) - 1.0,
                'close': base_price + (i * 0.1) + 0.5,
                'volume': 1000 + (i * 10),
            })

        return data


class ConfluenceScorerTest(TestCase):
    """Tests for ConfluenceScorer service."""

    def setUp(self):
        self.scorer = ConfluenceScorer()

    def test_calculate_detailed_score(self):
        """Test detailed score calculation."""
        voting_result = VotingResult(
            final_signal='buy',
            buy_votes=[
                VoteResult('c1', 'C1', 'buy', 80, 62.0, 3.8, {}),
                VoteResult('c2', 'C2', 'buy', 75, 68.0, 3.2, {}),
                VoteResult('c3', 'C3', 'buy', 85, 64.0, 3.5, {}),
                VoteResult('c4', 'C4', 'buy', 70, 66.0, 3.3, {}),
                VoteResult('c5', 'C5', 'buy', 90, 71.0, 3.0, {}),
            ],
            sell_votes=[],
            neutral_votes=[
                VoteResult('c6', 'C6', 'neutral', 0, 56.0, 4.1, {}),
                VoteResult('c7', 'C7', 'neutral', 0, 59.0, 3.8, {}),
                VoteResult('c8', 'C8', 'neutral', 0, 58.0, 4.5, {}),
            ],
            vote_count=5,
            threshold_met=True,
            confluence_score=75.0,
            average_confidence=80.0,
        )

        result = self.scorer.calculate_detailed_score(voting_result)

        self.assertIn('total_score', result)
        self.assertIn('strength_category', result)
        self.assertIn('vote_weight_score', result)
        self.assertIn('confidence_score', result)
        self.assertIn('win_rate_score', result)
        self.assertIn('risk_reward_score', result)
        self.assertIn('is_actionable', result)

        self.assertGreater(result['total_score'], 0)
        self.assertLessEqual(result['total_score'], 100)

    def test_vote_score_calculation(self):
        """Test vote weight score calculation."""
        votes_5 = [VoteResult('c', 'C', 'buy', 80, 60, 3.0, {})] * 5
        votes_8 = [VoteResult('c', 'C', 'buy', 80, 60, 3.0, {})] * 8

        score_5 = self.scorer._calculate_vote_score(votes_5)
        score_8 = self.scorer._calculate_vote_score(votes_8)

        self.assertLess(score_5.score, score_8.score)
        self.assertEqual(score_8.score, 100)

    def test_strength_category(self):
        """Test strength category determination."""
        self.assertEqual(
            self.scorer._get_strength_category(90), 'excellent'
        )
        self.assertEqual(
            self.scorer._get_strength_category(75), 'strong'
        )
        self.assertEqual(
            self.scorer._get_strength_category(55), 'moderate'
        )
        self.assertEqual(
            self.scorer._get_strength_category(35), 'weak'
        )
        self.assertEqual(
            self.scorer._get_strength_category(20), 'none'
        )


class SignalGeneratorTest(TestCase):
    """Tests for SignalGenerator service."""

    def setUp(self):
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
        self.generator = SignalGenerator(
            voting_threshold=5,
            min_confluence=50.0,
            min_confidence=60.0,
        )

    def test_initialization(self):
        """Test generator initialization."""
        self.assertEqual(self.generator.min_confluence, 50.0)
        self.assertEqual(self.generator.min_confidence, 60.0)

    def test_calculate_atr(self):
        """Test ATR calculation."""
        ohlcv_data = self._generate_mock_ohlcv(50)
        atr = self.generator._calculate_atr(ohlcv_data, period=14)

        self.assertGreater(atr, 0)

    def test_calculate_entry_levels_buy(self):
        """Test entry level calculation for buy."""
        from decimal import Decimal
        ohlcv_data = self._generate_mock_ohlcv(50)
        current_price = Decimal('100.00')

        levels = self.generator._calculate_entry_levels(
            'buy', current_price, ohlcv_data
        )

        self.assertEqual(levels['entry_price'], current_price)
        self.assertLess(levels['stop_loss'], current_price)
        self.assertGreater(levels['take_profit'], current_price)
        self.assertGreater(levels['risk_reward_ratio'], 0)

    def test_calculate_entry_levels_sell(self):
        """Test entry level calculation for sell."""
        from decimal import Decimal
        ohlcv_data = self._generate_mock_ohlcv(50)
        current_price = Decimal('100.00')

        levels = self.generator._calculate_entry_levels(
            'sell', current_price, ohlcv_data
        )

        self.assertEqual(levels['entry_price'], current_price)
        self.assertGreater(levels['stop_loss'], current_price)
        self.assertLess(levels['take_profit'], current_price)

    def _generate_mock_ohlcv(self, count=100):
        """Generate mock OHLCV data."""
        data = []
        base_price = 100.0
        base_time = datetime.now() - timedelta(hours=count)

        for i in range(count):
            data.append({
                'timestamp': base_time + timedelta(hours=i),
                'open': base_price + (i * 0.1),
                'high': base_price + (i * 0.1) + 2.0,
                'low': base_price + (i * 0.1) - 2.0,
                'close': base_price + (i * 0.1) + 0.5,
                'volume': 1000 + (i * 10),
            })

        return data


class MultiPairValidatorTest(TestCase):
    """Tests for MultiPairValidator service."""

    def setUp(self):
        self.validator = MultiPairValidator()
        self.exchange = Exchange.objects.create(
            name='binance',
            display_name='Binance',
        )
        self.trading_pair = TradingPair.objects.create(
            exchange=self.exchange,
            symbol='EUR/USD',
            base_currency='EUR',
            quote_currency='USD',
        )

    def test_evaluate_correlation_positive(self):
        """Test correlation evaluation for positive correlation."""
        # Same signal with positive correlation = confirm
        result = self.validator._evaluate_correlation('buy', 'buy', 0.8)
        self.assertEqual(result, 'confirm')

        # Different signal with positive correlation = contradict
        result = self.validator._evaluate_correlation('buy', 'sell', 0.8)
        self.assertEqual(result, 'contradict')

    def test_evaluate_correlation_negative(self):
        """Test correlation evaluation for negative correlation."""
        # Different signal with negative correlation = confirm
        result = self.validator._evaluate_correlation('buy', 'sell', -0.8)
        self.assertEqual(result, 'confirm')

        # Same signal with negative correlation = contradict
        result = self.validator._evaluate_correlation('buy', 'buy', -0.8)
        self.assertEqual(result, 'contradict')

    def test_evaluate_correlation_wait(self):
        """Test correlation evaluation with wait signal."""
        result = self.validator._evaluate_correlation('buy', 'wait', 0.8)
        self.assertEqual(result, 'neutral')

    def test_calculate_confidence_boost(self):
        """Test confidence boost calculation."""
        confirmations = [
            {'pair': 'GBP/USD', 'correlation': 0.8, 'signal': 'buy'},
            {'pair': 'AUD/USD', 'correlation': 0.7, 'signal': 'buy'},
        ]
        contradictions = []

        boost = self.validator._calculate_confidence_boost(
            confirmations, contradictions
        )
        self.assertEqual(boost, 4.0)  # 2 * 2.0

    def test_calculate_confidence_boost_with_contradictions(self):
        """Test confidence boost with contradictions."""
        confirmations = [
            {'pair': 'GBP/USD', 'correlation': 0.8, 'signal': 'buy'},
        ]
        contradictions = [
            {'pair': 'USD/JPY', 'correlation': -0.8, 'signal': 'sell'},
        ]

        boost = self.validator._calculate_confidence_boost(
            confirmations, contradictions
        )
        self.assertEqual(boost, -1.0)  # 2.0 - 3.0
