"""
Breakout Momentum Hunter - Combination 3.

Win Rate: 56%, Risk/Reward: 4.1:1

Indicators:
- Bollinger Bands(20,2)
- ADX(14)
- RSI(14)
- Volume Profile
- Linear Regression(50)

BUY Criteria:
1. Price breaks above Upper Bollinger Band
2. ADX < 25 before breakout, rising towards 25-30
3. RSI crosses above 50
4. Volume > 1.5x average
5. Linear Regression slope becomes positive
"""

from typing import Dict, Any, List, Tuple
from .base_combination import BaseCombination


class BreakoutMomentum(BaseCombination):
    """
    BREAKOUT MOMENTUM HUNTER

    Best for: After range consolidation, low volatility periods.
    Frequency: ~61 trades/year
    """

    def get_name(self) -> str:
        return 'breakout_momentum'

    def get_display_name(self) -> str:
        return 'Breakout Momentum Hunter'

    def get_win_rate(self) -> float:
        return 56.0

    def get_risk_reward_ratio(self) -> float:
        return 4.1

    def get_required_indicators(self) -> List[str]:
        return ['bollinger', 'adx', 'rsi', 'volume_profile', 'linear_regression']

    def evaluate_buy(self, indicators: Dict[str, Any]) -> Tuple[bool, int, Dict]:
        """Evaluate Breakout Momentum BUY criteria."""
        criteria = {}

        # Criterion 1: Price breaks above Upper BB
        bollinger = indicators.get('bollinger', {})
        if bollinger.get('upper') is not None:
            criteria['bollinger_breakout'] = bollinger.get('price_above_upper', False)
        else:
            criteria['bollinger_breakout'] = False

        # Criterion 2: ADX rising from < 25
        adx = indicators.get('adx', {})
        if adx.get('adx') is not None:
            adx_value = adx.get('adx', 0)
            # ADX in the 20-35 range (rising from low)
            criteria['adx_rising'] = 20 <= adx_value <= 35 and adx.get('is_bullish_trend', False)
        else:
            criteria['adx_rising'] = False

        # Criterion 3: RSI crosses above 50
        rsi = indicators.get('rsi', {})
        if rsi.get('rsi') is not None:
            rsi_value = rsi.get('rsi', 0)
            prev_rsi = rsi.get('previous_rsi', 0)
            criteria['rsi_bullish'] = rsi_value > 50 and prev_rsi <= 50
        else:
            criteria['rsi_bullish'] = False

        # Criterion 4: Volume confirmation (1.5x)
        volume = indicators.get('volume_profile', {})
        if volume.get('volume_ratio') is not None:
            criteria['volume_surge'] = volume.get('volume_ratio', 0) >= 1.5
        else:
            criteria['volume_surge'] = False

        # Criterion 5: Linear Regression slope positive
        lr = indicators.get('linear_regression', {})
        if lr.get('slope') is not None:
            criteria['lr_uptrend'] = lr.get('is_uptrend', False)
        else:
            criteria['lr_uptrend'] = False

        all_met = all(criteria.values())
        confidence = self._calculate_confidence(criteria)

        return all_met, confidence, criteria

    def evaluate_sell(self, indicators: Dict[str, Any]) -> Tuple[bool, int, Dict]:
        """Evaluate Breakout Momentum SELL criteria."""
        criteria = {}

        # Criterion 1: Price breaks below Lower BB
        bollinger = indicators.get('bollinger', {})
        if bollinger.get('lower') is not None:
            criteria['bollinger_breakout'] = bollinger.get('price_below_lower', False)
        else:
            criteria['bollinger_breakout'] = False

        # Criterion 2: ADX rising with bearish trend
        adx = indicators.get('adx', {})
        if adx.get('adx') is not None:
            adx_value = adx.get('adx', 0)
            criteria['adx_rising'] = 20 <= adx_value <= 35 and adx.get('is_bearish_trend', False)
        else:
            criteria['adx_rising'] = False

        # Criterion 3: RSI crosses below 50
        rsi = indicators.get('rsi', {})
        if rsi.get('rsi') is not None:
            rsi_value = rsi.get('rsi', 100)
            prev_rsi = rsi.get('previous_rsi', 100)
            criteria['rsi_bearish'] = rsi_value < 50 and prev_rsi >= 50
        else:
            criteria['rsi_bearish'] = False

        # Criterion 4: Volume confirmation
        volume = indicators.get('volume_profile', {})
        if volume.get('volume_ratio') is not None:
            criteria['volume_surge'] = volume.get('volume_ratio', 0) >= 1.5
        else:
            criteria['volume_surge'] = False

        # Criterion 5: Linear Regression slope negative
        lr = indicators.get('linear_regression', {})
        if lr.get('slope') is not None:
            criteria['lr_downtrend'] = lr.get('is_downtrend', False)
        else:
            criteria['lr_downtrend'] = False

        all_met = all(criteria.values())
        confidence = self._calculate_confidence(criteria)

        return all_met, confidence, criteria
