"""
Tests for signals app models.
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal

from apps.signals.models import Vote, SignalSession, Signal, ConfluenceScore
from apps.market_data.models import Exchange, TradingPair
from apps.combinations.models import Combination


class SignalSessionModelTest(TestCase):
    """Tests for SignalSession model."""

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
        self.session = SignalSession.objects.create(
            trading_pair=self.trading_pair,
            timeframe='1h',
            final_signal='buy',
            buy_votes=6,
            sell_votes=1,
            neutral_votes=1,
            voting_threshold=5,
            confluence_score=75.5,
            average_confidence=80.0,
        )

    def test_session_creation(self):
        """Test creating a signal session."""
        self.assertEqual(self.session.final_signal, 'buy')
        self.assertEqual(self.session.buy_votes, 6)
        self.assertEqual(self.session.voting_threshold, 5)

    def test_session_str(self):
        """Test string representation."""
        expected = "BTC/USD - buy (6B/1S)"
        self.assertEqual(str(self.session), expected)

    def test_total_votes_property(self):
        """Test total_votes property."""
        self.assertEqual(self.session.total_votes, 8)

    def test_is_actionable_property(self):
        """Test is_actionable property."""
        self.assertTrue(self.session.is_actionable)

        # Create wait session
        wait_session = SignalSession.objects.create(
            trading_pair=self.trading_pair,
            timeframe='1h',
            final_signal='wait',
            buy_votes=3,
            sell_votes=2,
            neutral_votes=3,
        )
        self.assertFalse(wait_session.is_actionable)

    def test_dominant_direction_property(self):
        """Test dominant_direction property."""
        self.assertEqual(self.session.dominant_direction, 'buy')

        # Sell dominant
        sell_session = SignalSession.objects.create(
            trading_pair=self.trading_pair,
            timeframe='1h',
            final_signal='sell',
            buy_votes=2,
            sell_votes=5,
            neutral_votes=1,
        )
        self.assertEqual(sell_session.dominant_direction, 'sell')


class SignalModelTest(TestCase):
    """Tests for Signal model."""

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
        self.session = SignalSession.objects.create(
            trading_pair=self.trading_pair,
            timeframe='1h',
            final_signal='buy',
            buy_votes=6,
            sell_votes=1,
            neutral_votes=1,
        )
        self.signal = Signal.objects.create(
            session=self.session,
            trading_pair=self.trading_pair,
            timeframe='1h',
            signal='buy',
            vote_count=6,
            confluence_score=75.5,
            confidence=80,
            entry_price=Decimal('50000.00'),
            stop_loss=Decimal('49000.00'),
            take_profit=Decimal('53000.00'),
            risk_reward_ratio=3.0,
            expires_at=timezone.now() + timezone.timedelta(hours=4),
        )

    def test_signal_creation(self):
        """Test creating a signal."""
        self.assertEqual(self.signal.signal, 'buy')
        self.assertEqual(self.signal.vote_count, 6)
        self.assertEqual(self.signal.status, 'pending')

    def test_signal_str(self):
        """Test string representation."""
        expected = "BTC/USD - buy (6/8)"
        self.assertEqual(str(self.signal), expected)

    def test_is_expired_property(self):
        """Test is_expired property."""
        self.assertFalse(self.signal.is_expired)

        # Create expired signal
        expired_signal = Signal.objects.create(
            session=self.session,
            trading_pair=self.trading_pair,
            timeframe='1h',
            signal='buy',
            vote_count=5,
            expires_at=timezone.now() - timezone.timedelta(hours=1),
        )
        self.assertTrue(expired_signal.is_expired)

    def test_mark_executed(self):
        """Test marking signal as executed."""
        self.signal.mark_executed()
        self.assertEqual(self.signal.status, 'executed')
        self.assertIsNotNone(self.signal.executed_at)

    def test_mark_expired(self):
        """Test marking signal as expired."""
        self.signal.mark_expired()
        self.assertEqual(self.signal.status, 'expired')

    def test_mark_cancelled(self):
        """Test marking signal as cancelled."""
        self.signal.mark_cancelled()
        self.assertEqual(self.signal.status, 'cancelled')


class VoteModelTest(TestCase):
    """Tests for Vote model."""

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
            name='golden_confluence',
            display_name='Golden Confluence',
            win_rate=62.0,
            risk_reward_ratio=3.8,
        )
        self.session = SignalSession.objects.create(
            trading_pair=self.trading_pair,
            timeframe='1h',
            final_signal='buy',
            buy_votes=1,
        )
        self.vote = Vote.objects.create(
            combination=self.combination,
            trading_pair=self.trading_pair,
            signal_session=self.session,
            timeframe='1h',
            signal='buy',
            confidence=85,
            criteria_met={'rsi_bullish': True, 'macd_bullish': True},
        )

    def test_vote_creation(self):
        """Test creating a vote."""
        self.assertEqual(self.vote.signal, 'buy')
        self.assertEqual(self.vote.confidence, 85)

    def test_vote_str(self):
        """Test string representation."""
        expected = "Golden Confluence - buy (85%)"
        self.assertEqual(str(self.vote), expected)

    def test_vote_criteria_met(self):
        """Test criteria_met JSON field."""
        self.assertTrue(self.vote.criteria_met['rsi_bullish'])
        self.assertTrue(self.vote.criteria_met['macd_bullish'])


class ConfluenceScoreModelTest(TestCase):
    """Tests for ConfluenceScore model."""

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
        self.session = SignalSession.objects.create(
            trading_pair=self.trading_pair,
            timeframe='1h',
            final_signal='buy',
            buy_votes=6,
        )
        self.confluence = ConfluenceScore.objects.create(
            session=self.session,
            trading_pair=self.trading_pair,
            timeframe='1h',
            total_score=75.5,
            vote_weight_score=30.0,
            confidence_score=20.0,
            win_rate_score=15.0,
            risk_reward_score=8.0,
            indicator_alignment_score=2.5,
        )

    def test_confluence_creation(self):
        """Test creating a confluence score."""
        self.assertEqual(self.confluence.total_score, 75.5)
        self.assertEqual(self.confluence.vote_weight_score, 30.0)

    def test_confluence_str(self):
        """Test string representation."""
        expected = "BTC/USD - Score: 75.5"
        self.assertEqual(str(self.confluence), expected)
