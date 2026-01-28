"""
CoinAPI Service - Integration with CoinAPI REST API.

This service handles communication with CoinAPI for historical
OHLCV data fetching. Migrated from the existing coinapi_service.py.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import requests
import logging

from apps.core.services.base_service import BaseService, ServiceResult


logger = logging.getLogger('trading_bot')


class CoinAPIService(BaseService):
    """
    Service for fetching data from CoinAPI.

    CoinAPI provides historical and real-time cryptocurrency
    and forex exchange rate data.

    Usage:
        service = CoinAPIService({'api_key': 'YOUR_KEY'})
        data = service.fetch_ohlcv('BTC/EUR', '1h', limit=100)
    """

    BASE_URL = 'https://rest.coinapi.io/v1'
    MAX_RESULTS_PER_REQUEST = 100

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__()
        self.config = config or {}
        self.api_key = self.config.get('api_key', '')
        self.headers = {
            'X-CoinAPI-Key': self.api_key,
            'Accept': 'application/json'
        }

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1h',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch OHLCV data from CoinAPI.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC/EUR', 'EURUSD')
            timeframe: Candle period ('15m', '1h', '4h', '1d')
            start_date: Start date for data
            end_date: End date for data
            limit: Maximum number of candles

        Returns:
            List of OHLCV dictionaries
        """
        # Convert symbol to CoinAPI format
        coinapi_symbol = self._format_symbol(symbol)
        period = self._format_timeframe(timeframe)

        # Build URL
        url = f"{self.BASE_URL}/ohlcv/{coinapi_symbol}/history"

        params = {
            'period_id': period,
            'limit': min(limit, self.MAX_RESULTS_PER_REQUEST)
        }

        if start_date:
            params['time_start'] = start_date.isoformat()
        if end_date:
            params['time_end'] = end_date.isoformat()

        try:
            self.log_info(f"Fetching OHLCV from CoinAPI: {coinapi_symbol}")

            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            data = response.json()

            # Transform to standard format
            result = []
            for candle in data:
                result.append({
                    'timestamp': datetime.fromisoformat(
                        candle['time_period_start'].replace('Z', '+00:00')
                    ),
                    'open': float(candle['price_open']),
                    'high': float(candle['price_high']),
                    'low': float(candle['price_low']),
                    'close': float(candle['price_close']),
                    'volume': float(candle.get('volume_traded', 0)),
                })

            self.log_info(f"Received {len(result)} candles from CoinAPI")
            return result

        except requests.exceptions.RequestException as e:
            self.log_error(f"CoinAPI request failed: {str(e)}", exc=e)
            return []
        except (KeyError, ValueError) as e:
            self.log_error(f"Error parsing CoinAPI response: {str(e)}", exc=e)
            return []

    def fetch_exchange_rate(
        self,
        base_currency: str,
        quote_currency: str
    ) -> Optional[Decimal]:
        """
        Fetch current exchange rate.

        Args:
            base_currency: Base currency (e.g., 'EUR')
            quote_currency: Quote currency (e.g., 'USD')

        Returns:
            Current exchange rate or None
        """
        url = f"{self.BASE_URL}/exchangerate/{base_currency}/{quote_currency}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            return Decimal(str(data['rate']))

        except Exception as e:
            self.log_error(f"Error fetching exchange rate: {str(e)}", exc=e)
            return None

    def fetch_extended_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetch extended historical data (for ranges > 100 days).

        Splits large date ranges into smaller chunks to respect API limits.

        Args:
            symbol: Trading pair symbol
            timeframe: Candle period
            start_date: Start date
            end_date: End date

        Returns:
            List of OHLCV dictionaries
        """
        all_data = []
        intervals = self._get_date_intervals(start_date, end_date)

        for interval_start, interval_end in intervals:
            data = self.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                start_date=interval_start,
                end_date=interval_end,
                limit=self.MAX_RESULTS_PER_REQUEST
            )
            all_data.extend(data)

        # Remove duplicates and sort
        seen = set()
        unique_data = []
        for candle in all_data:
            ts = candle['timestamp']
            if ts not in seen:
                seen.add(ts)
                unique_data.append(candle)

        unique_data.sort(key=lambda x: x['timestamp'])
        return unique_data

    def _format_symbol(self, symbol: str) -> str:
        """Convert symbol to CoinAPI format."""
        # Remove slash if present: EUR/USD -> EURUSD
        symbol = symbol.replace('/', '')

        # Add exchange prefix if needed
        # CoinAPI format: BITSTAMP_SPOT_BTC_EUR
        # For forex: FX_SPOT_EUR_USD
        if len(symbol) == 6:  # Forex pair like EURUSD
            base = symbol[:3]
            quote = symbol[3:]
            return f"FX_SPOT_{base}_{quote}"
        else:
            # Crypto - assume BTC pairs
            return f"BITSTAMP_SPOT_{symbol[:3]}_{symbol[3:]}"

    def _format_timeframe(self, timeframe: str) -> str:
        """Convert timeframe to CoinAPI period format."""
        mapping = {
            '15m': '15MIN',
            '1h': '1HRS',
            '4h': '4HRS',
            '1d': '1DAY',
        }
        return mapping.get(timeframe, '1HRS')

    def _get_date_intervals(
        self,
        start_date: datetime,
        end_date: datetime,
        interval_days: int = 90
    ) -> List[tuple]:
        """Split date range into intervals."""
        intervals = []
        current_start = start_date

        while current_start < end_date:
            current_end = min(
                current_start + timedelta(days=interval_days),
                end_date
            )
            intervals.append((current_start, current_end))
            current_start = current_end

        return intervals
