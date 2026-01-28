"""
CCI Indicator - Commodity Channel Index.

CCI measures the current price level relative to an average price
level over a given period of time.

Formula:
    Typical Price (TP) = (High + Low + Close) / 3
    CCI = (TP - SMA(TP)) / (0.015 * Mean Deviation)

Signals:
    - CCI > +100: Overbought
    - CCI < -100: Oversold
    - CCI crossing above 0: Bullish
    - CCI crossing below 0: Bearish
"""

from typing import Dict, Any, List
import numpy as np
from .base_indicator import BaseIndicator


class CCIIndicator(BaseIndicator):
    """
    Commodity Channel Index (CCI) indicator.

    Default period: 20

    Output:
        - cci: Current CCI value
        - previous_cci: Previous CCI value
        - is_overbought: CCI > 100
        - is_oversold: CCI < -100
    """

    def default_params(self) -> Dict[str, Any]:
        return {
            'period': 20,
            'overbought': 100,
            'oversold': -100,
            'constant': 0.015,
        }

    def calculate(self, ohlcv_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate CCI values."""
        period = self.params['period']
        constant = self.params['constant']

        if not self._validate_data(ohlcv_data, period):
            return {'cci': None, 'previous_cci': None}

        highs = self._extract_prices(ohlcv_data, 'high')
        lows = self._extract_prices(ohlcv_data, 'low')
        closes = self._extract_prices(ohlcv_data, 'close')

        # Calculate Typical Price
        typical_price = (highs + lows + closes) / 3

        # Calculate SMA of Typical Price
        tp_sma = self._sma(typical_price, period)

        # Calculate Mean Deviation
        mean_deviation = np.zeros_like(typical_price)
        mean_deviation[:period - 1] = np.nan

        for i in range(period - 1, len(typical_price)):
            window = typical_price[i - period + 1:i + 1]
            mean_deviation[i] = np.mean(np.abs(window - tp_sma[i]))

        # Calculate CCI
        cci = (typical_price - tp_sma) / (constant * mean_deviation)
        cci = np.where(mean_deviation != 0, cci, 0)

        current_cci = float(cci[-1])
        previous_cci = float(cci[-2]) if len(cci) > 1 else current_cci

        return {
            'cci': round(current_cci, 2),
            'previous_cci': round(previous_cci, 2),
            'is_overbought': current_cci > self.params['overbought'],
            'is_oversold': current_cci < self.params['oversold'],
            'is_positive': current_cci > 0,
            'is_rising': current_cci > previous_cci,
            'crossed_above_zero': previous_cci <= 0 and current_cci > 0,
            'crossed_below_zero': previous_cci >= 0 and current_cci < 0,
        }

    def get_signal(self, values: Dict[str, Any]) -> str:
        """
        Interpret CCI values as trading signal.

        Buy: CCI crosses above 0 from oversold
        Sell: CCI crosses below 0 from overbought
        """
        if values.get('cci') is None:
            return 'neutral'

        cci = values['cci']
        previous_cci = values['previous_cci']

        # Bullish crossover from oversold
        if values['crossed_above_zero'] and previous_cci < -50:
            return 'buy'

        # Bearish crossover from overbought
        if values['crossed_below_zero'] and previous_cci > 50:
            return 'sell'

        return 'neutral'

    def check_linear_regression_channel_buy(self, values: Dict[str, Any]) -> bool:
        """
        Check CCI criteria for Linear Regression Channel buy signal.

        Criteria: CCI > -100 (limit low) AND CCI rising
        """
        if values.get('cci') is None:
            return False

        return values['cci'] > -100 and values['is_rising']
