"""
ADX Indicator - Average Directional Index.

ADX measures trend strength (not direction). Used with +DI and -DI
to determine trend direction.

Components:
    - ADX: Trend strength (0-100)
    - +DI: Positive Directional Indicator
    - -DI: Negative Directional Indicator

Signals:
    - ADX > 25: Strong trend
    - ADX > 50: Very strong trend
    - ADX < 20: Weak/no trend (range market)
    - +DI > -DI: Bullish trend
    - +DI < -DI: Bearish trend
"""

from typing import Dict, Any, List
import numpy as np
from .base_indicator import BaseIndicator


class ADXIndicator(BaseIndicator):
    """
    Average Directional Index (ADX) indicator.

    Default period: 14

    Output:
        - adx: ADX value (0-100)
        - plus_di: +DI value
        - minus_di: -DI value
        - is_trending: ADX > 25
        - is_bullish_trend: +DI > -DI
    """

    def default_params(self) -> Dict[str, Any]:
        return {
            'period': 14,
            'trend_threshold': 25,
            'strong_trend_threshold': 50,
        }

    def calculate(self, ohlcv_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate ADX, +DI, and -DI values."""
        period = self.params['period']

        if not self._validate_data(ohlcv_data, period * 2):
            return {'adx': None, 'plus_di': None, 'minus_di': None}

        highs = self._extract_prices(ohlcv_data, 'high')
        lows = self._extract_prices(ohlcv_data, 'low')
        closes = self._extract_prices(ohlcv_data, 'close')

        # Calculate +DM and -DM
        high_diff = np.diff(highs)
        low_diff = -np.diff(lows)

        plus_dm = np.zeros(len(high_diff))
        minus_dm = np.zeros(len(high_diff))

        for i in range(len(high_diff)):
            if high_diff[i] > low_diff[i] and high_diff[i] > 0:
                plus_dm[i] = high_diff[i]
            if low_diff[i] > high_diff[i] and low_diff[i] > 0:
                minus_dm[i] = low_diff[i]

        # Calculate True Range
        tr = self._true_range(ohlcv_data)[1:]  # Skip first element

        # Smooth with Wilder's method
        smoothed_plus_dm = self._wilder_smooth(plus_dm, period)
        smoothed_minus_dm = self._wilder_smooth(minus_dm, period)
        smoothed_tr = self._wilder_smooth(tr, period)

        # Calculate +DI and -DI
        plus_di = 100 * smoothed_plus_dm / np.where(smoothed_tr != 0, smoothed_tr, 1)
        minus_di = 100 * smoothed_minus_dm / np.where(smoothed_tr != 0, smoothed_tr, 1)

        # Calculate DX
        di_sum = plus_di + minus_di
        di_diff = np.abs(plus_di - minus_di)
        dx = 100 * di_diff / np.where(di_sum != 0, di_sum, 1)

        # Calculate ADX (smoothed DX)
        adx = self._wilder_smooth(dx, period)

        current_adx = float(adx[-1])
        current_plus_di = float(plus_di[-1])
        current_minus_di = float(minus_di[-1])

        return {
            'adx': round(current_adx, 2),
            'plus_di': round(current_plus_di, 2),
            'minus_di': round(current_minus_di, 2),
            'is_trending': current_adx > self.params['trend_threshold'],
            'is_strong_trend': current_adx > self.params['strong_trend_threshold'],
            'is_bullish_trend': current_plus_di > current_minus_di,
            'is_bearish_trend': current_minus_di > current_plus_di,
            'trend_strength': 'strong' if current_adx > 50 else 'moderate' if current_adx > 25 else 'weak',
        }

    def _wilder_smooth(self, data: np.ndarray, period: int) -> np.ndarray:
        """Apply Wilder's smoothing method."""
        smoothed = np.zeros_like(data)
        smoothed[:period] = np.nan

        # Initial value
        smoothed[period - 1] = np.mean(data[:period])

        # Wilder's smoothing
        for i in range(period, len(data)):
            smoothed[i] = (smoothed[i - 1] * (period - 1) + data[i]) / period

        return smoothed

    def get_signal(self, values: Dict[str, Any]) -> str:
        """
        Interpret ADX values as trading signal.

        Buy: ADX > 25 AND +DI > -DI (strong bullish trend)
        Sell: ADX > 25 AND -DI > +DI (strong bearish trend)
        """
        if values.get('adx') is None:
            return 'neutral'

        is_trending = values['is_trending']
        is_bullish = values['is_bullish_trend']

        if is_trending and is_bullish:
            return 'buy'
        elif is_trending and not is_bullish:
            return 'sell'

        return 'neutral'

    def check_golden_confluence_buy(self, values: Dict[str, Any]) -> bool:
        """
        Check ADX criteria for Golden Confluence buy signal.

        Criteria: ADX > 25 AND +DI > -DI
        """
        if values.get('adx') is None:
            return False

        return values['is_trending'] and values['is_bullish_trend']

    def check_breakout_buy(self, values: Dict[str, Any], previous_adx: float = None) -> bool:
        """
        Check ADX criteria for Breakout Momentum buy signal.

        Criteria: ADX was < 25 before breakout, now rising towards 25-30
        """
        if values.get('adx') is None:
            return False

        adx = values['adx']

        if previous_adx is not None:
            # ADX was below 25 and is now rising
            return previous_adx < 25 and adx > previous_adx and adx >= 20

        return 20 <= adx <= 35
