"""
Linear Regression Indicator.

Linear Regression calculates the best-fit line through price data
and measures how well the data fits this line.

Components:
    - Regression Line: Best-fit line value
    - Slope: Direction and steepness of trend
    - R-squared (r^2): How well data fits the line (0-1)
    - Upper/Lower Channels: Standard deviation bands

Signals:
    - Positive slope: Uptrend
    - Negative slope: Downtrend
    - High r^2 (> 0.6): Strong trend
    - Price at lower channel: Potential buy
    - Price at upper channel: Potential sell
"""

from typing import Dict, Any, List
import numpy as np
from .base_indicator import BaseIndicator


class LinearRegressionIndicator(BaseIndicator):
    """
    Linear Regression indicator.

    Default period: 50

    Output:
        - regression_line: Current regression value
        - slope: Trend slope (normalized)
        - r_squared: R^2 coefficient (0-1)
        - upper_channel: Upper channel value
        - lower_channel: Lower channel value
    """

    def default_params(self) -> Dict[str, Any]:
        return {
            'period': 50,
            'channel_std': 2,  # Standard deviations for channel
            'slope_threshold': 0.02,  # Minimum slope for trend
            'r_squared_threshold': 0.6,  # Minimum r^2 for clear trend
        }

    def calculate(self, ohlcv_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate Linear Regression values."""
        period = self.params['period']
        channel_std = self.params['channel_std']

        if not self._validate_data(ohlcv_data, period):
            return {'regression_line': None, 'slope': None, 'r_squared': None}

        closes = self._extract_prices(ohlcv_data, 'close')
        current_close = float(closes[-1])

        # Use last 'period' points for regression
        y = closes[-period:]
        x = np.arange(period)

        # Linear regression using least squares
        n = len(x)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x ** 2)
        sum_y2 = np.sum(y ** 2)

        # Calculate slope and intercept
        denominator = n * sum_x2 - sum_x ** 2
        if denominator == 0:
            return {'regression_line': None, 'slope': None, 'r_squared': None}

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n

        # Calculate regression line value at current point
        regression_value = slope * (n - 1) + intercept

        # Calculate R-squared
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)

        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        # Calculate standard deviation of residuals for channels
        residuals = y - y_pred
        std_residual = np.std(residuals)

        upper_channel = regression_value + (channel_std * std_residual)
        lower_channel = regression_value - (channel_std * std_residual)

        # Normalize slope (percentage per period)
        normalized_slope = (slope / np.mean(y)) * 100 if np.mean(y) != 0 else 0

        return {
            'regression_line': round(float(regression_value), 5),
            'slope': round(float(normalized_slope), 4),
            'slope_raw': round(float(slope), 8),
            'r_squared': round(float(r_squared), 4),
            'upper_channel': round(float(upper_channel), 5),
            'lower_channel': round(float(lower_channel), 5),
            'current_close': round(current_close, 5),
            'is_uptrend': normalized_slope > self.params['slope_threshold'],
            'is_downtrend': normalized_slope < -self.params['slope_threshold'],
            'is_clear_trend': r_squared > self.params['r_squared_threshold'],
            'price_in_upper_zone': current_close > regression_value,
            'price_in_lower_zone': current_close < regression_value,
            'price_at_lower_channel': current_close <= lower_channel,
            'price_at_upper_channel': current_close >= upper_channel,
        }

    def get_signal(self, values: Dict[str, Any]) -> str:
        """
        Interpret Linear Regression as trading signal.

        Buy: Clear uptrend with price at lower channel
        Sell: Clear downtrend with price at upper channel
        """
        if values.get('regression_line') is None:
            return 'neutral'

        is_clear = values['is_clear_trend']

        if is_clear and values['is_uptrend'] and values['price_at_lower_channel']:
            return 'buy'
        elif is_clear and values['is_downtrend'] and values['price_at_upper_channel']:
            return 'sell'

        return 'neutral'

    def check_linear_regression_channel_buy(self, values: Dict[str, Any]) -> bool:
        """
        Check criteria for Linear Regression Channel buy signal.

        Criteria:
        - Slope > 0.02 (uptrend)
        - R^2 > 0.60 (clear trend)
        - Price bounces from lower channel
        """
        if values.get('regression_line') is None:
            return False

        return (
            values['is_uptrend'] and
            values['is_clear_trend'] and
            values['price_at_lower_channel']
        )

    def check_breakout_confirmation(self, values: Dict[str, Any]) -> bool:
        """
        Check if linear regression confirms a breakout.

        Used in Breakout Momentum Hunter combination.
        """
        if values.get('slope') is None:
            return False

        # Slope becomes positive after being near zero
        slope = values['slope']
        return slope > 0.02

    def detect_inflection(
        self,
        current_values: Dict[str, Any],
        previous_values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect slope inflection points.

        Used in Harmonic Confluence for divergence detection.
        """
        if current_values.get('slope') is None or previous_values.get('slope') is None:
            return {'bullish_inflection': False, 'bearish_inflection': False}

        current_slope = current_values['slope']
        previous_slope = previous_values['slope']

        # Bullish: slope changes from negative to near zero
        bullish = previous_slope < -0.01 and current_slope >= -0.01

        # Bearish: slope changes from positive to near zero
        bearish = previous_slope > 0.01 and current_slope <= 0.01

        return {
            'bullish_inflection': bullish,
            'bearish_inflection': bearish,
        }
