"""
RSI Indicator - Relative Strength Index.

RSI measures the speed and magnitude of recent price changes
to evaluate overbought or oversold conditions.

Formula:
    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss

Signals:
    - RSI < 30: Oversold (potential buy)
    - RSI > 70: Overbought (potential sell)
    - RSI > 50: Bullish momentum
    - RSI < 50: Bearish momentum
"""

from typing import Dict, Any, List
import numpy as np
from .base_indicator import BaseIndicator


class RSIIndicator(BaseIndicator):
    """
    Relative Strength Index (RSI) indicator.

    Default period: 14

    Output:
        - rsi: Current RSI value (0-100)
        - previous_rsi: Previous RSI value
        - is_overbought: RSI > 70
        - is_oversold: RSI < 30
    """

    def default_params(self) -> Dict[str, Any]:
        return {
            'period': 14,
            'overbought': 70,
            'oversold': 30,
        }

    def calculate(self, ohlcv_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate RSI values."""
        period = self.params['period']

        if not self._validate_data(ohlcv_data, period + 1):
            return {'rsi': None, 'previous_rsi': None}

        closes = self._extract_prices(ohlcv_data, 'close')
        deltas = np.diff(closes)

        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        # Calculate average gain and loss
        avg_gain = np.zeros(len(gains))
        avg_loss = np.zeros(len(gains))

        # Initial SMA for first period
        avg_gain[period - 1] = np.mean(gains[:period])
        avg_loss[period - 1] = np.mean(losses[:period])

        # Smooth with Wilder's method
        for i in range(period, len(gains)):
            avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i]) / period
            avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i]) / period

        # Calculate RS and RSI
        rs = np.where(avg_loss != 0, avg_gain / avg_loss, 0)
        rsi = 100 - (100 / (1 + rs))

        current_rsi = float(rsi[-1])
        previous_rsi = float(rsi[-2]) if len(rsi) > 1 else current_rsi

        return {
            'rsi': round(current_rsi, 2),
            'previous_rsi': round(previous_rsi, 2),
            'is_overbought': current_rsi > self.params['overbought'],
            'is_oversold': current_rsi < self.params['oversold'],
            'is_ascending': current_rsi > previous_rsi,
            'rsi_series': [round(float(v), 2) for v in rsi[-10:]],  # Last 10 values
        }

    def get_signal(self, values: Dict[str, Any]) -> str:
        """
        Interpret RSI values as trading signal.

        Buy signal: RSI < 30 and ascending (oversold recovery)
        Sell signal: RSI > 70 and descending (overbought reversal)
        """
        if values.get('rsi') is None:
            return 'neutral'

        rsi = values['rsi']
        previous_rsi = values.get('previous_rsi', rsi)

        # Oversold recovery = potential buy
        if rsi < self.params['oversold'] and rsi > previous_rsi:
            return 'buy'

        # Overbought reversal = potential sell
        if rsi > self.params['overbought'] and rsi < previous_rsi:
            return 'sell'

        return 'neutral'

    def check_golden_confluence_buy(self, values: Dict[str, Any]) -> bool:
        """
        Check RSI criteria for Golden Confluence buy signal.

        Criteria: RSI > 50 AND RSI ascending from < 30 zone
        """
        if values.get('rsi') is None:
            return False

        rsi = values['rsi']
        previous_rsi = values.get('previous_rsi', rsi)

        return rsi > 50 and previous_rsi < 30

    def check_mean_reversion_buy(self, values: Dict[str, Any]) -> bool:
        """
        Check RSI criteria for Mean Reversion buy signal.

        Criteria: RSI < 30 (oversold)
        """
        if values.get('rsi') is None:
            return False

        return values['rsi'] < 30

    def check_mean_reversion_sell(self, values: Dict[str, Any]) -> bool:
        """
        Check RSI criteria for Mean Reversion sell signal.

        Criteria: RSI > 70 (overbought)
        """
        if values.get('rsi') is None:
            return False

        return values['rsi'] > 70
