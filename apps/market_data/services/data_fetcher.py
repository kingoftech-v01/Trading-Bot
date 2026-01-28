"""
Data Fetcher Service - Orchestrates data collection from various sources.

This service coordinates data fetching from multiple exchange APIs
and manages data storage in the database.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from django.utils import timezone
from apps.core.services.base_service import BaseService, ServiceResult
from ..models import Exchange, TradingPair, OHLCV


logger = logging.getLogger('trading_bot')


class DataFetcher(BaseService):
    """
    Service for fetching market data from exchange APIs.

    Supports:
    - CoinAPI (REST)
    - Binance (CCXT)
    - MetaTrader 5

    Usage:
        fetcher = DataFetcher()
        result = fetcher.fetch_ohlcv(
            trading_pair=pair,
            timeframe='1h',
            limit=100
        )
    """

    def __init__(self):
        super().__init__()
        self._api_clients = {}

    def fetch_ohlcv(
        self,
        trading_pair: TradingPair,
        timeframe: str = '1h',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> ServiceResult:
        """
        Fetch OHLCV data for a trading pair.

        Args:
            trading_pair: TradingPair model instance
            timeframe: Candle timeframe ('15m', '1h', '4h', '1d')
            start_date: Start date for data fetch
            end_date: End date for data fetch
            limit: Maximum number of candles to fetch

        Returns:
            ServiceResult with list of OHLCV records
        """
        try:
            exchange = trading_pair.exchange

            # Get the appropriate API client
            client = self._get_api_client(exchange)
            if not client:
                return ServiceResult.fail(
                    f"No API client available for exchange: {exchange.name}"
                )

            # Fetch data from API
            self.log_info(
                f"Fetching OHLCV data for {trading_pair.symbol} {timeframe}",
                trading_pair=trading_pair.symbol,
                timeframe=timeframe,
                limit=limit
            )

            raw_data = client.fetch_ohlcv(
                symbol=trading_pair.symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )

            if not raw_data:
                return ServiceResult.fail("No data returned from API")

            # Save to database
            saved_records = self._save_ohlcv_data(
                trading_pair=trading_pair,
                timeframe=timeframe,
                data=raw_data
            )

            self.log_info(
                f"Saved {len(saved_records)} OHLCV records for {trading_pair.symbol}",
                count=len(saved_records)
            )

            return ServiceResult.ok(data={'count': len(saved_records)})

        except Exception as e:
            self.log_error(f"Error fetching OHLCV data: {str(e)}", exc=e)
            return ServiceResult.fail(f"Error fetching data: {str(e)}")

    def fetch_all_pairs(
        self,
        timeframe: str = '1h',
        limit: int = 100
    ) -> ServiceResult:
        """
        Fetch OHLCV data for all active trading pairs.

        Args:
            timeframe: Candle timeframe
            limit: Maximum candles per pair

        Returns:
            ServiceResult with summary of fetch operations
        """
        pairs = TradingPair.objects.filter(
            is_active=True,
            exchange__is_enabled=True
        ).select_related('exchange')

        results = {
            'success': [],
            'failed': [],
        }

        for pair in pairs:
            result = self.fetch_ohlcv(
                trading_pair=pair,
                timeframe=timeframe,
                limit=limit
            )

            if result.success:
                results['success'].append(pair.symbol)
            else:
                results['failed'].append({
                    'symbol': pair.symbol,
                    'error': result.error
                })

        return ServiceResult.ok(data=results)

    def _get_api_client(self, exchange: Exchange):
        """Get or create API client for an exchange."""
        if exchange.id not in self._api_clients:
            if exchange.api_type == Exchange.API_TYPE_REST:
                if 'coinapi' in exchange.name.lower():
                    from .coinapi_service import CoinAPIService
                    self._api_clients[exchange.id] = CoinAPIService(exchange.config)
                else:
                    # Generic REST client
                    return None
            elif exchange.api_type == Exchange.API_TYPE_WEBSOCKET:
                # CCXT client for exchanges like Binance
                return None
            elif exchange.api_type == Exchange.API_TYPE_MT5:
                # MetaTrader 5 client
                return None

        return self._api_clients.get(exchange.id)

    def _save_ohlcv_data(
        self,
        trading_pair: TradingPair,
        timeframe: str,
        data: List[Dict[str, Any]]
    ) -> List[OHLCV]:
        """
        Save OHLCV data to database.

        Uses bulk_create with ignore_conflicts for efficiency.
        """
        records = []

        for candle in data:
            records.append(OHLCV(
                trading_pair=trading_pair,
                timeframe=timeframe,
                timestamp=candle['timestamp'],
                open=Decimal(str(candle['open'])),
                high=Decimal(str(candle['high'])),
                low=Decimal(str(candle['low'])),
                close=Decimal(str(candle['close'])),
                volume=Decimal(str(candle.get('volume', 0))),
            ))

        # Bulk insert, ignoring duplicates
        OHLCV.objects.bulk_create(
            records,
            ignore_conflicts=True,
            batch_size=500
        )

        return records

    def get_latest_timestamp(
        self,
        trading_pair: TradingPair,
        timeframe: str
    ) -> Optional[datetime]:
        """Get the timestamp of the latest OHLCV record for a pair."""
        try:
            latest = OHLCV.objects.filter(
                trading_pair=trading_pair,
                timeframe=timeframe
            ).latest('timestamp')
            return latest.timestamp
        except OHLCV.DoesNotExist:
            return None
