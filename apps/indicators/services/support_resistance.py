"""
Support/Resistance Indicator.

Identifies key price levels where buying or selling pressure
has historically been significant.

Methods:
    - Pivot points
    - Recent highs/lows
    - Price clusters

Uses:
    - Stop-loss placement
    - Take-profit targets
    - Entry confirmation
"""

from typing import Dict, Any, List
import numpy as np
from .base_indicator import BaseIndicator


class SupportResistanceIndicator(BaseIndicator):
    """
    Support and Resistance level indicator.

    Default period: 20

    Output:
        - support_levels: List of support levels
        - resistance_levels: List of resistance levels
        - nearest_support: Closest support below price
        - nearest_resistance: Closest resistance above price
    """

    def default_params(self) -> Dict[str, Any]:
        return {
            'period': 20,
            'touch_threshold': 0.001,  # Price must be within 0.1% to count
            'min_touches': 2,  # Minimum touches to be significant
        }

    def calculate(self, ohlcv_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate Support and Resistance levels."""
        period = self.params['period']

        if not self._validate_data(ohlcv_data, period):
            return {
                'support_levels': [],
                'resistance_levels': [],
            }

        highs = self._extract_prices(ohlcv_data, 'high')
        lows = self._extract_prices(ohlcv_data, 'low')
        closes = self._extract_prices(ohlcv_data, 'close')

        current_close = float(closes[-1])

        # Find pivot points (swing highs and lows)
        support_levels = []
        resistance_levels = []

        # Look for swing lows (potential support)
        for i in range(2, len(lows) - 2):
            if (lows[i] < lows[i - 1] and lows[i] < lows[i - 2] and
                lows[i] < lows[i + 1] and lows[i] < lows[i + 2]):
                support_levels.append(float(lows[i]))

        # Look for swing highs (potential resistance)
        for i in range(2, len(highs) - 2):
            if (highs[i] > highs[i - 1] and highs[i] > highs[i - 2] and
                highs[i] > highs[i + 1] and highs[i] > highs[i + 2]):
                resistance_levels.append(float(highs[i]))

        # Also add recent high/low of the period
        period_high = float(np.max(highs[-period:]))
        period_low = float(np.min(lows[-period:]))

        if period_high not in resistance_levels:
            resistance_levels.append(period_high)
        if period_low not in support_levels:
            support_levels.append(period_low)

        # Sort and remove duplicates (within threshold)
        support_levels = self._cluster_levels(sorted(set(support_levels)))
        resistance_levels = self._cluster_levels(sorted(set(resistance_levels), reverse=True))

        # Find nearest levels
        supports_below = [s for s in support_levels if s < current_close]
        resistances_above = [r for r in resistance_levels if r > current_close]

        nearest_support = max(supports_below) if supports_below else None
        nearest_resistance = min(resistances_above) if resistances_above else None

        return {
            'support_levels': [round(s, 5) for s in support_levels[-5:]],  # Last 5
            'resistance_levels': [round(r, 5) for r in resistance_levels[:5]],  # Top 5
            'nearest_support': round(nearest_support, 5) if nearest_support else None,
            'nearest_resistance': round(nearest_resistance, 5) if nearest_resistance else None,
            'current_close': round(current_close, 5),
            'period_high': round(period_high, 5),
            'period_low': round(period_low, 5),
            'price_above_support': nearest_support is not None,
            'distance_to_support': round(
                (current_close - nearest_support) / current_close * 100, 2
            ) if nearest_support else None,
            'distance_to_resistance': round(
                (nearest_resistance - current_close) / current_close * 100, 2
            ) if nearest_resistance else None,
        }

    def _cluster_levels(self, levels: List[float], threshold: float = 0.005) -> List[float]:
        """Cluster nearby levels into single levels."""
        if not levels:
            return []

        clustered = [levels[0]]

        for level in levels[1:]:
            # Check if this level is close to the last clustered level
            if abs(level - clustered[-1]) / clustered[-1] > threshold:
                clustered.append(level)
            else:
                # Merge by averaging
                clustered[-1] = (clustered[-1] + level) / 2

        return clustered

    def get_signal(self, values: Dict[str, Any]) -> str:
        """
        S/R levels don't directly generate signals.

        They're used for stop-loss placement and confirming signals.
        """
        return 'neutral'

    def get_stop_loss_level(
        self,
        values: Dict[str, Any],
        direction: str = 'buy',
        buffer_pips: float = 10
    ) -> float:
        """
        Get stop-loss level based on S/R.

        Args:
            values: S/R calculation results
            direction: 'buy' or 'sell'
            buffer_pips: Additional buffer in pips

        Returns:
            Recommended stop-loss level
        """
        if direction == 'buy':
            # Stop below nearest support
            support = values.get('nearest_support')
            if support:
                return round(support - (buffer_pips * 0.0001), 5)
            # Fallback: use period low
            return round(values['period_low'] - (buffer_pips * 0.0001), 5)
        else:
            # Stop above nearest resistance
            resistance = values.get('nearest_resistance')
            if resistance:
                return round(resistance + (buffer_pips * 0.0001), 5)
            # Fallback: use period high
            return round(values['period_high'] + (buffer_pips * 0.0001), 5)

    def check_stochastic_crossover_buy(self, values: Dict[str, Any]) -> bool:
        """
        Check S/R criteria for Stochastic Crossover buy signal.

        Criteria: Price above support level (not in extreme low zone)
        """
        if values.get('nearest_support') is None:
            return True  # No support found, assume OK

        return values['price_above_support']
