"""
Tests for signals app API endpoints.
"""

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import timedelta

from apps.signals.models import Vote, SignalSession, Signal, ConfluenceScore
from apps.market_data.models import Exchange, TradingPair, OHLCV
from apps.combinations.models import Combination


class SignalSessionAPITest(APITestCase):
    """Tests for SignalSession API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
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
            confluence_score=75.5,
        )

    def test_list_sessions(self):
        """Test listing sessions."""
        url = '/api/v1/signals/sessions/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_session(self):
        """Test retrieving a single session."""
        url = f'/api/v1/signals/sessions/{self.session.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['final_signal'], 'buy')

    def test_actionable_sessions(self):
        """Test getting actionable sessions."""
        url = '/api/v1/signals/sessions/actionable/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SignalAPITest(APITestCase):
    """Tests for Signal API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
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
            expires_at=timezone.now() + timedelta(hours=4),
        )

    def test_list_signals(self):
        """Test listing signals."""
        url = '/api/v1/signals/signals/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_signal(self):
        """Test retrieving a single signal."""
        url = f'/api/v1/signals/signals/{self.signal.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['signal'], 'buy')

    def test_active_signals(self):
        """Test getting active signals."""
        url = '/api/v1/signals/signals/active/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_execute_signal(self):
        """Test executing a signal."""
        url = f'/api/v1/signals/signals/{self.signal.id}/execute/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'executed')

    def test_cancel_signal(self):
        """Test cancelling a signal."""
        # Create new signal for cancel test
        signal = Signal.objects.create(
            session=self.session,
            trading_pair=self.trading_pair,
            timeframe='1h',
            signal='buy',
            vote_count=5,
            expires_at=timezone.now() + timedelta(hours=4),
        )
        url = f'/api/v1/signals/signals/{signal.id}/cancel/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'cancelled')


class GenerateSignalAPITest(APITestCase):
    """Tests for signal generation API."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
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

        # Create OHLCV data
        base_time = timezone.now() - timedelta(hours=200)
        for i in range(200):
            OHLCV.objects.create(
                trading_pair=self.trading_pair,
                timeframe='1h',
                timestamp=base_time + timedelta(hours=i),
                open=Decimal('100') + Decimal(str(i * 0.1)),
                high=Decimal('101') + Decimal(str(i * 0.1)),
                low=Decimal('99') + Decimal(str(i * 0.1)),
                close=Decimal('100.5') + Decimal(str(i * 0.1)),
                volume=Decimal('1000') + Decimal(str(i)),
            )

    def test_generate_signal(self):
        """Test generating a signal."""
        url = '/api/v1/signals/generate/'
        data = {
            'trading_pair_id': str(self.trading_pair.id),
            'timeframe': '1h',
            'min_confluence': 50.0,
            'min_confidence': 60.0,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('signal_generated', response.data)
        self.assertIn('voting_summary', response.data)

    def test_generate_signal_invalid_pair(self):
        """Test generating signal with invalid pair."""
        url = '/api/v1/signals/generate/'
        data = {
            'trading_pair_id': '00000000-0000-0000-0000-000000000000',
            'timeframe': '1h',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_voting_status(self):
        """Test getting voting status."""
        url = '/api/v1/signals/voting-status/'
        data = {
            'trading_pair_id': str(self.trading_pair.id),
            'timeframe': '1h',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('voting_summary', response.data)
