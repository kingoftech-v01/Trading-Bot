"""
Volume Profile Indicator.

Volume Profile analyzes trading activity at specific price levels
to identify areas of high and low trading interest.

Components:
    - Volume at price levels
    - Point of Control (POC): Highest volume price
    - Value Area: Price range with 70% of volume
    - Volume confirmation for signals

Uses:
    - Confirm breakouts with volume
    - Identify support/resistance levels
    - Validate price moves
"""

from typing import Dict, Any, List
import numpy as np
from .base_indicator import BaseIndicator


class VolumeProfileIndicator(BaseIndicator):
    """
    Volume Profile indicator.

    Default period: 20

    Output:
        - current_volume: Current period volume
        - average_volume: Average volume
        - volume_ratio: Current / Average
        - is_high_volume: Volume > 1.5 * average
        - is_low_volume: Volume < 0.5 * average
    """

    def default_params(self) -> Dict[str, Any]:
        return {
            'period': 20,
            'high_volume_threshold': 1.5,
            'low_volume_threshold': 0.5,
            'confirmation_threshold': 1.2,  # Volume increase for confirmation
        }

    def calculate(self, ohlcv_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate Volume Profile values."""
        period = self.params['period']

        if not self._validate_data(ohlcv_data, period):
            return {'current_volume': None, 'average_volume': None}

        volumes = np.array([float(d.get('volume', 0)) for d in ohlcv_data])

        current_volume = float(volumes[-1])
        average_volume = float(np.mean(volumes[-period:]))
        previous_volume = float(volumes[-2]) if len(volumes) > 1 else current_volume

        volume_ratio = current_volume / average_volume if average_volume != 0 else 1

        # Calculate volume trend
        recent_avg = np.mean(volumes[-5:]) if len(volumes) >= 5 else current_volume
        older_avg = np.mean(volumes[-10:-5]) if len(volumes) >= 10 else recent_avg

        return {
            'current_volume': round(current_volume, 2),
            'previous_volume': round(previous_volume, 2),
            'average_volume': round(average_volume, 2),
            'volume_ratio': round(volume_ratio, 2),
            'is_high_volume': volume_ratio > self.params['high_volume_threshold'],
            'is_low_volume': volume_ratio < self.params['low_volume_threshold'],
            'is_increasing': current_volume > previous_volume,
            'volume_trend': 'increasing' if recent_avg > older_avg else 'decreasing',
            'confirms_move': volume_ratio > self.params['confirmation_threshold'],
        }

    def get_signal(self, values: Dict[str, Any]) -> str:
        """
        Volume alone doesn't generate signals.

        It's used to confirm other indicator signals.
        """
        return 'neutral'

    def confirms_breakout(self, values: Dict[str, Any]) -> bool:
        """
        Check if volume confirms a breakout.

        Used in Breakout Momentum Hunter combination.
        Criteria: Volume > 1.5 * average (50%+ increase)
        """
        if values.get('volume_ratio') is None:
            return False

        return values['volume_ratio'] >= 1.5

    def confirms_mean_reversion(self, values: Dict[str, Any]) -> bool:
        """
        Check if volume confirms mean reversion signal.

        Criteria: Volume > average (confirmation by volume)
        """
        if values.get('volume_ratio') is None:
            return False

        return values['volume_ratio'] > 1.0

    def confirms_signal(self, values: Dict[str, Any]) -> bool:
        """
        General check if volume confirms any signal.

        Criteria: Volume >= confirmation threshold
        """
        if values.get('confirms_move') is None:
            return False

        return values['confirms_move']
