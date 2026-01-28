"""
Stochastic Oscillator Indicator.

Stochastic compares a closing price to its price range over a period.

Components:
    - %K: Main line (fast)
    - %D: Signal line (SMA of %K)

Formula:
    %K = (Close - Lowest Low) / (Highest High - Lowest Low) * 100
    %D = SMA(%K, d_period)

Signals:
    - K% < 20: Oversold
    - K% > 80: Overbought
    - K% crosses above D%: Bullish
    - K% crosses below D%: Bearish
"""

from typing import Dict, Any, List
import numpy as np
from .base_indicator import BaseIndicator


class StochasticIndicator(BaseIndicator):
    """
    Stochastic Oscillator indicator.

    Default parameters: 14, 3, 3 (standard)
    Alternative: 20, 5, 5 (slow stochastic)

    Output:
        - k: %K value (0-100)
        - d: %D value (0-100)
        - previous_k: Previous %K
        - previous_d: Previous %D
        - is_overbought: K% > 80
        - is_oversold: K% < 20
    """

    def default_params(self) -> Dict[str, Any]:
        return {
            'k_period': 14,
            'k_smooth': 3,
            'd_period': 3,
            'overbought': 80,
            'oversold': 20,
        }

    def calculate(self, ohlcv_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate Stochastic %K and %D values."""
        k_period = self.params['k_period']
        k_smooth = self.params['k_smooth']
        d_period = self.params['d_period']

        min_periods = k_period + k_smooth + d_period
        if not self._validate_data(ohlcv_data, min_periods):
            return {'k': None, 'd': None}

        highs = self._extract_prices(ohlcv_data, 'high')
        lows = self._extract_prices(ohlcv_data, 'low')
        closes = self._extract_prices(ohlcv_data, 'close')

        # Calculate raw %K
        raw_k = np.zeros(len(closes))
        raw_k[:k_period - 1] = np.nan

        for i in range(k_period - 1, len(closes)):
            lowest_low = np.min(lows[i - k_period + 1:i + 1])
            highest_high = np.max(highs[i - k_period + 1:i + 1])

            if highest_high != lowest_low:
                raw_k[i] = ((closes[i] - lowest_low) /
                           (highest_high - lowest_low)) * 100
            else:
                raw_k[i] = 50  # Neutral when range is zero

        # Smooth %K
        k = self._sma(raw_k, k_smooth)

        # Calculate %D (SMA of smoothed %K)
        d = self._sma(k, d_period)

        current_k = float(k[-1])
        current_d = float(d[-1])
        previous_k = float(k[-2]) if len(k) > 1 else current_k
        previous_d = float(d[-2]) if len(d) > 1 else current_d

        return {
            'k': round(current_k, 2),
            'd': round(current_d, 2),
            'previous_k': round(previous_k, 2),
            'previous_d': round(previous_d, 2),
            'is_overbought': current_k > self.params['overbought'],
            'is_oversold': current_k < self.params['oversold'],
            'k_above_d': current_k > current_d,
            'k_crossed_above_d': previous_k <= previous_d and current_k > current_d,
            'k_crossed_below_d': previous_k >= previous_d and current_k < current_d,
        }

    def get_signal(self, values: Dict[str, Any]) -> str:
        """
        Interpret Stochastic values as trading signal.

        Buy: K% crosses above D% from oversold zone
        Sell: K% crosses below D% from overbought zone
        """
        if values.get('k') is None:
            return 'neutral'

        k = values['k']
        k_crossed_above = values['k_crossed_above_d']
        k_crossed_below = values['k_crossed_below_d']

        # Bullish crossover from oversold
        if k_crossed_above and k < 50:
            return 'buy'

        # Bearish crossover from overbought
        if k_crossed_below and k > 50:
            return 'sell'

        return 'neutral'

    def check_golden_confluence_buy(self, values: Dict[str, Any]) -> bool:
        """
        Check Stochastic criteria for Golden Confluence buy signal.

        Criteria: K% > D% with K% < 80 (not overbought)
        """
        if values.get('k') is None:
            return False

        return values['k_above_d'] and not values['is_overbought']

    def check_mean_reversion_buy(self, values: Dict[str, Any]) -> bool:
        """
        Check Stochastic criteria for Mean Reversion buy signal.

        Criteria: K% < 20 AND D% < 30 (oversold)
        """
        if values.get('k') is None:
            return False

        return values['k'] < 20 and values['d'] < 30

    def check_stochastic_crossover_buy(
        self,
        fast_values: Dict[str, Any],
        slow_values: Dict[str, Any]
    ) -> bool:
        """
        Check criteria for Stochastic Crossover System.

        Uses two stochastics: fast (14,3,3) and slow (20,5,5)
        Criteria: Fast K% crosses above Slow K%
        """
        if fast_values.get('k') is None or slow_values.get('k') is None:
            return False

        fast_k = fast_values['k']
        slow_k = slow_values['k']
        fast_prev_k = fast_values['previous_k']
        slow_prev_k = slow_values['previous_k']

        # Fast K% crosses above Slow K%
        crossed_above = fast_prev_k <= slow_prev_k and fast_k > slow_k

        return crossed_above
