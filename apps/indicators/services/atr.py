"""
ATR Indicator - Average True Range.

ATR measures market volatility by decomposing the entire range
of an asset price for a period.

Formula:
    True Range = max(High - Low, |High - Prev Close|, |Low - Prev Close|)
    ATR = EMA(True Range, period)

Uses:
    - Volatility measurement
    - Position sizing adjustment
    - Stop-loss placement
    - Detecting volatility spikes
"""

from typing import Dict, Any, List
import numpy as np
from .base_indicator import BaseIndicator


class ATRIndicator(BaseIndicator):
    """
    Average True Range (ATR) indicator.

    Default period: 14

    Output:
        - atr: Current ATR value
        - atr_percent: ATR as percentage of price
        - is_high_volatility: ATR > 1.5 * average ATR
        - is_low_volatility: ATR < 0.7 * average ATR
    """

    def default_params(self) -> Dict[str, Any]:
        return {
            'period': 14,
            'high_volatility_threshold': 1.5,
            'low_volatility_threshold': 0.7,
        }

    def calculate(self, ohlcv_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate ATR values."""
        period = self.params['period']

        if not self._validate_data(ohlcv_data, period + 1):
            return {'atr': None, 'atr_percent': None}

        # Calculate True Range
        tr = self._true_range(ohlcv_data)

        # Calculate ATR using Wilder's smoothing
        atr = np.zeros_like(tr)
        atr[:period] = np.nan

        # Initial ATR is simple average
        atr[period - 1] = np.mean(tr[:period])

        # Wilder's smoothing
        for i in range(period, len(tr)):
            atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period

        current_atr = float(atr[-1])
        current_close = float(self._extract_prices(ohlcv_data, 'close')[-1])

        # Calculate average ATR over recent period
        recent_atr = np.nanmean(atr[-period * 2:])

        # ATR as percentage of price
        atr_percent = (current_atr / current_close) * 100 if current_close != 0 else 0

        # Volatility classification
        high_threshold = self.params['high_volatility_threshold']
        low_threshold = self.params['low_volatility_threshold']

        return {
            'atr': round(current_atr, 5),
            'atr_percent': round(atr_percent, 4),
            'average_atr': round(float(recent_atr), 5),
            'is_high_volatility': current_atr > recent_atr * high_threshold,
            'is_low_volatility': current_atr < recent_atr * low_threshold,
            'volatility_ratio': round(current_atr / recent_atr if recent_atr != 0 else 1, 2),
            'current_close': round(current_close, 5),
        }

    def get_signal(self, values: Dict[str, Any]) -> str:
        """
        ATR doesn't generate trading signals directly.

        It's used for position sizing and volatility assessment.
        """
        return 'neutral'

    def calculate_stop_loss(
        self,
        values: Dict[str, Any],
        entry_price: float,
        direction: str = 'buy',
        multiplier: float = 2.0
    ) -> float:
        """
        Calculate stop-loss level using ATR.

        Args:
            values: ATR calculation results
            entry_price: Entry price
            direction: 'buy' or 'sell'
            multiplier: ATR multiplier (default 2.0)

        Returns:
            Stop-loss price level
        """
        if values.get('atr') is None:
            return entry_price

        atr = values['atr']
        stop_distance = atr * multiplier

        if direction == 'buy':
            return round(entry_price - stop_distance, 5)
        else:
            return round(entry_price + stop_distance, 5)

    def adjust_position_size(
        self,
        values: Dict[str, Any],
        base_size: float
    ) -> float:
        """
        Adjust position size based on volatility.

        High volatility: Reduce size
        Low volatility: Increase size (slightly)

        Args:
            values: ATR calculation results
            base_size: Base position size

        Returns:
            Adjusted position size
        """
        if values.get('volatility_ratio') is None:
            return base_size

        ratio = values['volatility_ratio']

        if ratio > 1.5:
            # High volatility - reduce size by 30%
            return base_size * 0.7
        elif ratio > 1.2:
            # Moderate high volatility - reduce size by 15%
            return base_size * 0.85
        elif ratio < 0.7:
            # Low volatility - increase size by 20%
            return base_size * 1.2
        else:
            return base_size
