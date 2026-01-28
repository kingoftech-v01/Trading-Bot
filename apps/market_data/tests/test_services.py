"""
Tests for Market Data Services.

Tests DataFetcher, CoinAPIService, and DataCleaner services.
"""

from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock

from apps.market_data.models import Exchange, TradingPair, OHLCV
from apps.market_data.services.data_cleaner import DataCleaner


class DataCleanerTestCase(TestCase):
    """Test cases for DataCleaner service."""

    def setUp(self):
        self.cleaner = DataCleaner()

    def test_remove_duplicates(self):
        """Test duplicate removal."""
        now = timezone.now()
        data = [
            {'timestamp': now, 'open': 1.0, 'high': 1.1, 'low': 0.9, 'close': 1.05},
            {'timestamp': now, 'open': 1.0, 'high': 1.1, 'low': 0.9, 'close': 1.05},  # duplicate
            {'timestamp': now + timedelta(hours=1), 'open': 1.05, 'high': 1.15, 'low': 0.95, 'close': 1.1},
        ]

        cleaned = self.cleaner.clean(data)
        self.assertEqual(len(cleaned), 2)

    def test_validate_ohlcv_valid(self):
        """Test OHLCV validation with valid data."""
        now = timezone.now()
        data = [
            {'timestamp': now, 'open': 1.0, 'high': 1.1, 'low': 0.9, 'close': 1.05},
        ]

        cleaned = self.cleaner.clean(data)
        self.assertEqual(len(cleaned), 1)

    def test_validate_ohlcv_invalid_high_low(self):
        """Test OHLCV validation with invalid high < low."""
        now = timezone.now()
        data = [
            {'timestamp': now, 'open': 1.0, 'high': 0.9, 'low': 1.1, 'close': 1.05},  # high < low
        ]

        cleaned = self.cleaner.clean(data)
        self.assertEqual(len(cleaned), 0)

    def test_detect_gaps(self):
        """Test gap detection."""
        now = timezone.now()
        data = [
            {'timestamp': now, 'open': 1.0, 'high': 1.1, 'low': 0.9, 'close': 1.05},
            {'timestamp': now + timedelta(hours=3), 'open': 1.05, 'high': 1.15, 'low': 0.95, 'close': 1.1},  # 2h gap
        ]

        gaps = self.cleaner.detect_gaps(data, timeframe_minutes=60)
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0]['missing_candles'], 2)

    def test_calculate_atr(self):
        """Test ATR calculation."""
        now = timezone.now()
        data = []

        # Generate 20 candles
        for i in range(20):
            data.append({
                'timestamp': now + timedelta(hours=i),
                'open': 1.0 + i * 0.001,
                'high': 1.01 + i * 0.001,
                'low': 0.99 + i * 0.001,
                'close': 1.005 + i * 0.001,
            })

        atrs = self.cleaner.calculate_atr(data, period=14)
        self.assertTrue(len(atrs) > 0)
        self.assertTrue(all(atr > 0 for atr in atrs))


class CoinAPIServiceTestCase(TestCase):
    """Test cases for CoinAPIService."""

    @patch('apps.market_data.services.coinapi_service.requests.get')
    def test_fetch_ohlcv_success(self, mock_get):
        """Test successful OHLCV fetch."""
        from apps.market_data.services.coinapi_service import CoinAPIService

        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                'time_period_start': '2024-01-01T00:00:00.0000000Z',
                'price_open': 1.0850,
                'price_high': 1.0900,
                'price_low': 1.0800,
                'price_close': 1.0875,
                'volume_traded': 1000,
            }
        ]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        service = CoinAPIService({'api_key': 'test_key'})
        data = service.fetch_ohlcv('EUR/USD', '1h', limit=1)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['open'], 1.0850)
        self.assertEqual(data[0]['close'], 1.0875)

    def test_format_symbol_forex(self):
        """Test symbol formatting for forex."""
        from apps.market_data.services.coinapi_service import CoinAPIService

        service = CoinAPIService()
        formatted = service._format_symbol('EUR/USD')
        self.assertEqual(formatted, 'FX_SPOT_EUR_USD')

    def test_format_timeframe(self):
        """Test timeframe formatting."""
        from apps.market_data.services.coinapi_service import CoinAPIService

        service = CoinAPIService()
        self.assertEqual(service._format_timeframe('15m'), '15MIN')
        self.assertEqual(service._format_timeframe('1h'), '1HRS')
        self.assertEqual(service._format_timeframe('4h'), '4HRS')
        self.assertEqual(service._format_timeframe('1d'), '1DAY')
