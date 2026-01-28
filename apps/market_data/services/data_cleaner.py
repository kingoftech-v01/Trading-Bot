"""
Data Cleaner Service - Validates and cleans OHLCV data.

This service handles data quality:
- Detecting and handling gaps
- Removing inconsistent values
- Normalizing data formats
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import logging

from apps.core.services.base_service import BaseService, ServiceResult


logger = logging.getLogger('trading_bot')


class DataCleaner(BaseService):
    """
    Service for cleaning and validating OHLCV data.

    Handles:
    - Gap detection and filling
    - Outlier detection
    - Data normalization
    - Consistency checks

    Usage:
        cleaner = DataCleaner()
        clean_data = cleaner.clean(raw_data)
    """

    # Threshold for detecting inconsistent values
    INCONSISTENCY_THRESHOLD = 10.0  # 10x normal range

    def __init__(self):
        super().__init__()

    def clean(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean and validate OHLCV data.

        Args:
            data: List of OHLCV dictionaries

        Returns:
            Cleaned list of OHLCV dictionaries
        """
        if not data:
            return []

        # Sort by timestamp
        data = sorted(data, key=lambda x: x['timestamp'])

        # Remove duplicates
        data = self._remove_duplicates(data)

        # Remove inconsistent values
        data = self._remove_inconsistent_values(data)

        # Validate OHLCV relationships
        data = self._validate_ohlcv(data)

        self.log_info(f"Cleaned data: {len(data)} records")
        return data

    def _remove_duplicates(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate timestamps."""
        seen = set()
        unique = []

        for candle in data:
            ts = candle['timestamp']
            if ts not in seen:
                seen.add(ts)
                unique.append(candle)

        removed = len(data) - len(unique)
        if removed > 0:
            self.log_info(f"Removed {removed} duplicate records")

        return unique

    def _remove_inconsistent_values(
        self,
        data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove records with inconsistent values.

        A value is inconsistent if it differs by more than
        INCONSISTENCY_THRESHOLD from its neighbors.
        """
        if len(data) < 3:
            return data

        clean = []

        for i, candle in enumerate(data):
            if self._is_inconsistent(candle, data, i):
                self.log_debug(
                    f"Removed inconsistent candle at {candle['timestamp']}"
                )
                continue
            clean.append(candle)

        removed = len(data) - len(clean)
        if removed > 0:
            self.log_info(f"Removed {removed} inconsistent records")

        return clean

    def _is_inconsistent(
        self,
        candle: Dict[str, Any],
        data: List[Dict[str, Any]],
        index: int
    ) -> bool:
        """Check if a candle has inconsistent values."""
        # Skip first and last candles
        if index == 0 or index == len(data) - 1:
            return False

        prev_candle = data[index - 1]
        next_candle = data[index + 1]

        # Calculate expected range based on neighbors
        expected_close = (prev_candle['close'] + next_candle['close']) / 2
        expected_range = abs(next_candle['close'] - prev_candle['close'])

        if expected_range == 0:
            expected_range = prev_candle['close'] * 0.01  # 1% default

        # Check if current close is too far from expected
        actual_diff = abs(candle['close'] - expected_close)
        ratio = actual_diff / expected_range if expected_range > 0 else 0

        return ratio > self.INCONSISTENCY_THRESHOLD

    def _validate_ohlcv(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate OHLCV relationships.

        Ensures:
        - high >= max(open, close)
        - low <= min(open, close)
        - high >= low
        """
        valid = []

        for candle in data:
            open_price = candle['open']
            high = candle['high']
            low = candle['low']
            close = candle['close']

            # Check basic OHLCV relationships
            if high < low:
                self.log_debug(
                    f"Invalid OHLCV at {candle['timestamp']}: high < low"
                )
                continue

            if high < max(open_price, close):
                self.log_debug(
                    f"Invalid OHLCV at {candle['timestamp']}: high < max(open, close)"
                )
                continue

            if low > min(open_price, close):
                self.log_debug(
                    f"Invalid OHLCV at {candle['timestamp']}: low > min(open, close)"
                )
                continue

            valid.append(candle)

        return valid

    def detect_gaps(
        self,
        data: List[Dict[str, Any]],
        timeframe_minutes: int
    ) -> List[Dict[str, Any]]:
        """
        Detect gaps in the data.

        Args:
            data: Sorted list of OHLCV dictionaries
            timeframe_minutes: Expected minutes between candles

        Returns:
            List of gap information dictionaries
        """
        gaps = []
        expected_delta = timedelta(minutes=timeframe_minutes)

        for i in range(1, len(data)):
            prev_ts = data[i - 1]['timestamp']
            curr_ts = data[i]['timestamp']
            actual_delta = curr_ts - prev_ts

            if actual_delta > expected_delta * 1.5:  # Allow 50% tolerance
                gaps.append({
                    'start': prev_ts,
                    'end': curr_ts,
                    'missing_candles': int(actual_delta / expected_delta) - 1
                })

        if gaps:
            self.log_info(f"Detected {len(gaps)} gaps in data")

        return gaps

    def calculate_atr(
        self,
        data: List[Dict[str, Any]],
        period: int = 14
    ) -> List[float]:
        """
        Calculate Average True Range for volatility analysis.

        Used for detecting abnormal volatility and adjusting
        inconsistency thresholds.
        """
        if len(data) < period + 1:
            return []

        true_ranges = []
        atrs = []

        for i in range(1, len(data)):
            high = data[i]['high']
            low = data[i]['low']
            prev_close = data[i - 1]['close']

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)

        # Calculate ATR using simple moving average
        for i in range(period - 1, len(true_ranges)):
            atr = sum(true_ranges[i - period + 1:i + 1]) / period
            atrs.append(atr)

        return atrs
