"""
MACD Indicator - Moving Average Convergence Divergence.

MACD shows the relationship between two moving averages of a security's price.

Components:
    - MACD Line: 12-period EMA - 26-period EMA
    - Signal Line: 9-period EMA of MACD Line
    - Histogram: MACD Line - Signal Line

Signals:
    - MACD Line > Signal Line: Bullish
    - MACD Line < Signal Line: Bearish
    - Histogram > 0 and growing: Strong bullish momentum
    - Histogram < 0 and shrinking: Strong bearish momentum
"""

from typing import Dict, Any, List
import numpy as np
from .base_indicator import BaseIndicator


class MACDIndicator(BaseIndicator):
    """
    Moving Average Convergence Divergence (MACD) indicator.

    Default parameters: 12, 26, 9

    Output:
        - macd_line: MACD line value
        - signal_line: Signal line value
        - histogram: Histogram value
        - previous_histogram: Previous histogram value
        - is_bullish: MACD line > signal line
    """

    def default_params(self) -> Dict[str, Any]:
        return {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9,
        }

    def calculate(self, ohlcv_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate MACD values."""
        fast = self.params['fast_period']
        slow = self.params['slow_period']
        signal = self.params['signal_period']

        min_periods = slow + signal
        if not self._validate_data(ohlcv_data, min_periods):
            return {
                'macd_line': None,
                'signal_line': None,
                'histogram': None,
            }

        closes = self._extract_prices(ohlcv_data, 'close')

        # Calculate EMAs
        ema_fast = self._ema(closes, fast)
        ema_slow = self._ema(closes, slow)

        # MACD Line
        macd_line = ema_fast - ema_slow

        # Signal Line (EMA of MACD)
        signal_line = self._ema(macd_line[~np.isnan(macd_line)], signal)

        # Pad signal line to match length
        signal_padded = np.full(len(closes), np.nan)
        signal_padded[-len(signal_line):] = signal_line

        # Histogram
        histogram = macd_line - signal_padded

        current_macd = float(macd_line[-1])
        current_signal = float(signal_padded[-1])
        current_hist = float(histogram[-1])
        previous_hist = float(histogram[-2]) if len(histogram) > 1 else current_hist

        return {
            'macd_line': round(current_macd, 6),
            'signal_line': round(current_signal, 6),
            'histogram': round(current_hist, 6),
            'previous_histogram': round(previous_hist, 6),
            'is_bullish': current_macd > current_signal,
            'histogram_growing': current_hist > previous_hist,
            'histogram_positive': current_hist > 0,
            'macd_series': [round(float(v), 6) for v in macd_line[-10:]],
        }

    def get_signal(self, values: Dict[str, Any]) -> str:
        """
        Interpret MACD values as trading signal.

        Buy: MACD > Signal AND Histogram > 0 and growing
        Sell: MACD < Signal AND Histogram < 0 and shrinking
        """
        if values.get('macd_line') is None:
            return 'neutral'

        is_bullish = values['is_bullish']
        hist_positive = values['histogram_positive']
        hist_growing = values['histogram_growing']

        if is_bullish and hist_positive and hist_growing:
            return 'buy'
        elif not is_bullish and not hist_positive and not hist_growing:
            return 'sell'

        return 'neutral'

    def check_golden_confluence_buy(self, values: Dict[str, Any]) -> bool:
        """
        Check MACD criteria for Golden Confluence buy signal.

        Criteria: MACD Line > Signal Line AND Histogram > 0 and growing
        """
        if values.get('macd_line') is None:
            return False

        return (
            values['is_bullish'] and
            values['histogram_positive'] and
            values['histogram_growing']
        )

    def detect_divergence(
        self,
        ohlcv_data: List[Dict[str, Any]],
        lookback: int = 14
    ) -> Dict[str, Any]:
        """
        Detect MACD divergence patterns.

        Bullish divergence: Price makes lower lows, MACD makes higher lows
        Bearish divergence: Price makes higher highs, MACD makes lower highs

        Used in Harmonic Confluence combination.
        """
        if len(ohlcv_data) < lookback + 1:
            return {'bullish_divergence': False, 'bearish_divergence': False}

        closes = self._extract_prices(ohlcv_data, 'close')
        full_result = self.calculate(ohlcv_data)

        if full_result.get('macd_line') is None:
            return {'bullish_divergence': False, 'bearish_divergence': False}

        # Get recent price and MACD lows/highs
        recent_closes = closes[-lookback:]
        macd_series = full_result.get('macd_series', [])

        if len(macd_series) < 2:
            return {'bullish_divergence': False, 'bearish_divergence': False}

        # Simple divergence check (would need more sophisticated implementation)
        price_trend = recent_closes[-1] - recent_closes[0]
        macd_trend = macd_series[-1] - macd_series[0]

        bullish_divergence = price_trend < 0 and macd_trend > 0
        bearish_divergence = price_trend > 0 and macd_trend < 0

        return {
            'bullish_divergence': bullish_divergence,
            'bearish_divergence': bearish_divergence,
        }
