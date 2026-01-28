"""
Bollinger Bands Indicator.

Bollinger Bands consist of a middle band (SMA) and two outer bands
at standard deviations above and below.

Components:
    - Middle Band: 20-period SMA
    - Upper Band: Middle + (2 * Standard Deviation)
    - Lower Band: Middle - (2 * Standard Deviation)

Signals:
    - Price near lower band: Potential support/buy
    - Price near upper band: Potential resistance/sell
    - Band squeeze: Low volatility, potential breakout
    - Band expansion: High volatility
"""

from typing import Dict, Any, List
import numpy as np
from .base_indicator import BaseIndicator


class BollingerBandsIndicator(BaseIndicator):
    """
    Bollinger Bands indicator.

    Default parameters: 20, 2

    Output:
        - upper: Upper band value
        - middle: Middle band (SMA)
        - lower: Lower band value
        - bandwidth: Band width percentage
        - percent_b: %B (price position within bands)
    """

    def default_params(self) -> Dict[str, Any]:
        return {
            'period': 20,
            'std_dev': 2,
        }

    def calculate(self, ohlcv_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate Bollinger Bands values."""
        period = self.params['period']
        std_multiplier = self.params['std_dev']

        if not self._validate_data(ohlcv_data, period):
            return {'upper': None, 'middle': None, 'lower': None}

        closes = self._extract_prices(ohlcv_data, 'close')
        current_close = float(closes[-1])

        # Calculate middle band (SMA)
        middle = self._sma(closes, period)

        # Calculate standard deviation
        std = np.zeros_like(closes)
        std[:period - 1] = np.nan

        for i in range(period - 1, len(closes)):
            std[i] = np.std(closes[i - period + 1:i + 1])

        # Calculate bands
        upper = middle + (std_multiplier * std)
        lower = middle - (std_multiplier * std)

        current_upper = float(upper[-1])
        current_middle = float(middle[-1])
        current_lower = float(lower[-1])

        # Calculate bandwidth
        bandwidth = ((current_upper - current_lower) / current_middle) * 100

        # Calculate %B (where price is within bands)
        if current_upper != current_lower:
            percent_b = (current_close - current_lower) / (current_upper - current_lower)
        else:
            percent_b = 0.5

        return {
            'upper': round(current_upper, 5),
            'middle': round(current_middle, 5),
            'lower': round(current_lower, 5),
            'bandwidth': round(bandwidth, 2),
            'percent_b': round(percent_b, 4),
            'current_close': round(current_close, 5),
            'price_above_middle': current_close > current_middle,
            'price_near_upper': percent_b > 0.8,
            'price_near_lower': percent_b < 0.2,
            'price_above_upper': current_close > current_upper,
            'price_below_lower': current_close < current_lower,
        }

    def get_signal(self, values: Dict[str, Any]) -> str:
        """
        Interpret Bollinger Bands as trading signal.

        Buy: Price bounces off lower band
        Sell: Price bounces off upper band
        """
        if values.get('upper') is None:
            return 'neutral'

        if values['price_near_lower']:
            return 'buy'
        elif values['price_near_upper']:
            return 'sell'

        return 'neutral'

    def check_golden_confluence_buy(self, values: Dict[str, Any]) -> bool:
        """
        Check Bollinger criteria for Golden Confluence buy signal.

        Criteria: Price > Lower Band AND visible bounce
        """
        if values.get('lower') is None:
            return False

        close = values['current_close']
        lower = values['lower']

        # Price should be above lower band (bouncing)
        # and below middle (not overextended)
        return close > lower and not values['price_above_middle']

    def check_mean_reversion_buy(self, values: Dict[str, Any]) -> bool:
        """
        Check Bollinger criteria for Mean Reversion buy signal.

        Criteria: Price < Lower Band (oversold condition)
        """
        if values.get('lower') is None:
            return False

        return values['price_below_lower']

    def check_breakout_buy(self, values: Dict[str, Any]) -> bool:
        """
        Check Bollinger criteria for Breakout buy signal.

        Criteria: Price breaks above upper band with close > upper
        """
        if values.get('upper') is None:
            return False

        return values['price_above_upper']

    def is_squeeze(self, values: Dict[str, Any], threshold: float = 10.0) -> bool:
        """
        Check if bands are in squeeze (low volatility).

        Squeeze often precedes breakout moves.
        """
        if values.get('bandwidth') is None:
            return False

        return values['bandwidth'] < threshold
