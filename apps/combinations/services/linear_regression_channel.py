"""
Linear Regression Channel Play - Combination 5.

Win Rate: 59%, Risk/Reward: 3.8:1

Indicators:
- Linear Regression(50)
- RSI(14)
- ADX(14)
- Bollinger Bands(20,2)
- CCI(20)

BUY Criteria:
1. LR slope > 0.02 (uptrend)
2. R² > 0.60 (clear trend)
3. Price bounces from lower channel
4. RSI in 30-50 zone
5. ADX > 20
6. CCI > -100 and rising
"""

from typing import Dict, Any, List, Tuple
from .base_combination import BaseCombination


class LinearRegressionChannel(BaseCombination):
    """
    LINEAR REGRESSION CHANNEL PLAY

    Best for: Trending markets with clear channels.
    Frequency: ~82 trades/year
    """

    def get_name(self) -> str:
        return 'linear_regression_channel'

    def get_display_name(self) -> str:
        return 'Linear Regression Channel Play'

    def get_win_rate(self) -> float:
        return 59.0

    def get_risk_reward_ratio(self) -> float:
        return 3.8

    def get_required_indicators(self) -> List[str]:
        return ['linear_regression', 'rsi', 'adx', 'bollinger', 'cci']

    def evaluate_buy(self, indicators: Dict[str, Any]) -> Tuple[bool, int, Dict]:
        """Evaluate Linear Regression Channel BUY criteria."""
        criteria = {}

        # Criterion 1: LR slope > 0.02
        lr = indicators.get('linear_regression', {})
        if lr.get('slope') is not None:
            criteria['lr_uptrend'] = lr.get('is_uptrend', False)
        else:
            criteria['lr_uptrend'] = False

        # Criterion 2: R² > 0.60
        if lr.get('r_squared') is not None:
            criteria['lr_clear_trend'] = lr.get('is_clear_trend', False)
        else:
            criteria['lr_clear_trend'] = False

        # Criterion 3: Price at lower channel
        if lr.get('lower_channel') is not None:
            criteria['price_at_channel'] = lr.get('price_at_lower_channel', False)
        else:
            criteria['price_at_channel'] = False

        # Criterion 4: RSI in 30-50 zone
        rsi = indicators.get('rsi', {})
        if rsi.get('rsi') is not None:
            rsi_value = rsi.get('rsi', 0)
            criteria['rsi_zone'] = 30 <= rsi_value <= 50
        else:
            criteria['rsi_zone'] = False

        # Criterion 5: ADX > 20
        adx = indicators.get('adx', {})
        if adx.get('adx') is not None:
            criteria['adx_trending'] = adx.get('adx', 0) > 20
        else:
            criteria['adx_trending'] = False

        # Criterion 6: CCI > -100 and rising
        cci = indicators.get('cci', {})
        if cci.get('cci') is not None:
            criteria['cci_rising'] = (
                cci.get('cci', -200) > -100 and
                cci.get('is_rising', False)
            )
        else:
            criteria['cci_rising'] = False

        all_met = all(criteria.values())
        confidence = self._calculate_confidence(criteria)

        return all_met, confidence, criteria

    def evaluate_sell(self, indicators: Dict[str, Any]) -> Tuple[bool, int, Dict]:
        """Evaluate Linear Regression Channel SELL criteria."""
        criteria = {}

        # LR slope < -0.02
        lr = indicators.get('linear_regression', {})
        if lr.get('slope') is not None:
            criteria['lr_downtrend'] = lr.get('is_downtrend', False)
        else:
            criteria['lr_downtrend'] = False

        # R² > 0.60
        if lr.get('r_squared') is not None:
            criteria['lr_clear_trend'] = lr.get('is_clear_trend', False)
        else:
            criteria['lr_clear_trend'] = False

        # Price at upper channel
        if lr.get('upper_channel') is not None:
            criteria['price_at_channel'] = lr.get('price_at_upper_channel', False)
        else:
            criteria['price_at_channel'] = False

        # RSI in 50-70 zone
        rsi = indicators.get('rsi', {})
        if rsi.get('rsi') is not None:
            rsi_value = rsi.get('rsi', 100)
            criteria['rsi_zone'] = 50 <= rsi_value <= 70
        else:
            criteria['rsi_zone'] = False

        # ADX > 20
        adx = indicators.get('adx', {})
        if adx.get('adx') is not None:
            criteria['adx_trending'] = adx.get('adx', 0) > 20
        else:
            criteria['adx_trending'] = False

        # CCI < 100 and falling
        cci = indicators.get('cci', {})
        if cci.get('cci') is not None:
            criteria['cci_falling'] = (
                cci.get('cci', 200) < 100 and
                not cci.get('is_rising', True)
            )
        else:
            criteria['cci_falling'] = False

        all_met = all(criteria.values())
        confidence = self._calculate_confidence(criteria)

        return all_met, confidence, criteria
