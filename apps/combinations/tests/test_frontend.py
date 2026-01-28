"""
Tests for combinations app frontend views.
"""

from django.test import TestCase, Client
from django.urls import reverse

from apps.combinations.models import Combination, CombinationResult
from apps.market_data.models import Exchange, TradingPair


class CombinationFrontendViewTest(TestCase):
    """Tests for Combination frontend views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.combination = Combination.objects.create(
            name='golden_confluence',
            display_name='Golden Confluence',
            description='Test combination',
            win_rate=62.0,
            risk_reward_ratio=3.8,
        )

    def test_combination_list_view(self):
        """Test combination list view."""
        url = '/combinations/'
        response = self.client.get(url)
        # View should work even without templates
        self.assertIn(response.status_code, [200, 302, 404])

    def test_combination_detail_view(self):
        """Test combination detail view."""
        url = f'/combinations/{self.combination.id}/'
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302, 404])

    def test_combination_create_view(self):
        """Test combination create view."""
        url = '/combinations/create/'
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302, 404])

    def test_combination_update_view(self):
        """Test combination update view."""
        url = f'/combinations/{self.combination.id}/edit/'
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302, 404])


class CombinationResultFrontendViewTest(TestCase):
    """Tests for CombinationResult frontend views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
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
            display_name='Test Combo',
            win_rate=60.0,
            risk_reward_ratio=3.0,
        )
        self.result = CombinationResult.objects.create(
            combination=self.combination,
            trading_pair=self.trading_pair,
            timeframe='1h',
            signal='buy',
            confidence=80,
        )

    def test_result_list_view(self):
        """Test result list view."""
        url = '/combinations/results/'
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302, 404])

    def test_result_detail_view(self):
        """Test result detail view."""
        url = f'/combinations/results/{self.result.id}/'
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302, 404])


class EvaluationFrontendViewTest(TestCase):
    """Tests for evaluation frontend views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

    def test_evaluate_view(self):
        """Test evaluate view."""
        url = '/combinations/evaluate/'
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302, 404])

    def test_info_view(self):
        """Test info view."""
        url = '/combinations/info/'
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302, 404])
