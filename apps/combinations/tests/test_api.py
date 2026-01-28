"""
Tests for combinations app API endpoints.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.combinations.models import Combination, CombinationResult
from apps.market_data.models import Exchange, TradingPair, OHLCV
from datetime import datetime, timedelta


class CombinationAPITest(APITestCase):
    """Tests for Combination API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.combination = Combination.objects.create(
            name='golden_confluence',
            display_name='Golden Confluence',
            description='Test combination',
            win_rate=62.0,
            risk_reward_ratio=3.8,
        )

    def test_list_combinations(self):
        """Test listing combinations."""
        url = '/api/v1/combinations/combinations/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_retrieve_combination(self):
        """Test retrieving a single combination."""
        url = f'/api/v1/combinations/combinations/{self.combination.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'golden_confluence')

    def test_create_combination(self):
        """Test creating a combination."""
        url = '/api/v1/combinations/combinations/'
        data = {
            'name': 'new_combo',
            'display_name': 'New Combination',
            'description': 'A new test combination',
            'win_rate': 55.0,
            'risk_reward_ratio': 3.0,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'new_combo')

    def test_update_combination(self):
        """Test updating a combination."""
        url = f'/api/v1/combinations/combinations/{self.combination.id}/'
        data = {
            'name': 'golden_confluence',
            'display_name': 'Updated Golden',
            'win_rate': 65.0,
            'risk_reward_ratio': 4.0,
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['display_name'], 'Updated Golden')

    def test_delete_combination(self):
        """Test deleting a combination."""
        url = f'/api/v1/combinations/combinations/{self.combination.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_combination_info_action(self):
        """Test getting combination info."""
        url = f'/api/v1/combinations/combinations/{self.combination.id}/info/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CombinationResultAPITest(APITestCase):
    """Tests for CombinationResult API endpoints."""

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

    def test_list_results(self):
        """Test listing results."""
        url = '/api/v1/combinations/results/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_result(self):
        """Test retrieving a single result."""
        url = f'/api/v1/combinations/results/{self.result.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['signal'], 'buy')

    def test_filter_results_by_signal(self):
        """Test filtering results by signal."""
        url = '/api/v1/combinations/results/?signal=buy'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class EvaluationAPITest(APITestCase):
    """Tests for evaluation API endpoints."""

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
        base_time = datetime.now() - timedelta(hours=200)
        for i in range(200):
            OHLCV.objects.create(
                trading_pair=self.trading_pair,
                timeframe='1h',
                timestamp=base_time + timedelta(hours=i),
                open=100 + i * 0.1,
                high=101 + i * 0.1,
                low=99 + i * 0.1,
                close=100.5 + i * 0.1,
                volume=1000 + i,
            )

    def test_evaluate_all_combinations(self):
        """Test evaluating all combinations."""
        url = '/api/v1/combinations/evaluate-all/'
        data = {
            'trading_pair_id': str(self.trading_pair.id),
            'timeframe': '1h',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('buy_votes', response.data)
        self.assertIn('sell_votes', response.data)
        self.assertIn('summary', response.data)

    def test_evaluate_all_invalid_pair(self):
        """Test evaluating with invalid trading pair."""
        url = '/api/v1/combinations/evaluate-all/'
        data = {
            'trading_pair_id': '00000000-0000-0000-0000-000000000000',
            'timeframe': '1h',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_combination_info_endpoint(self):
        """Test getting combination info."""
        url = '/api/v1/combinations/info/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 8)
