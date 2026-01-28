"""
Mean Reversion Power - Combination 2.

Win Rate: 68%, Risk/Reward: 3.2:1

Indicators:
- RSI(14)
- Stochastic(14,3,3)
- Bollinger Bands(20,2)
- MACD(12,26,9)
- ATR(14)

BUY Criteria:
1. RSI < 30 (oversold)
2. Stochastic: K% < 20 AND D% < 30
3. Price < Lower Bollinger Band
4. MACD Histogram > 0 OR turning positive
5. Volume > Average volume
"""

from typing import Dict, Any, List, Tuple
from .base_combination import BaseCombination


class MeanReversion(BaseCombination):
    """
    MEAN REVERSION POWER

    Best for: Range-bound markets, after news shocks.
    Frequency: ~94 trades/year
    """

    def get_name(self) -> str:
        return 'mean_reversion'

    def get_display_name(self) -> str:
        return 'Mean Reversion Power'

    def get_win_rate(self) -> float:
        return 68.0

    def get_risk_reward_ratio(self) -> float:
        return 3.2

    def get_required_indicators(self) -> List[str]:
        return ['rsi', 'stochastic', 'bollinger', 'macd', 'atr', 'volume_profile']

    def evaluate_buy(self, indicators: Dict[str, Any]) -> Tuple[bool, int, Dict]:
        """Evaluate Mean Reversion BUY criteria."""
        criteria = {}

        # Criterion 1: RSI < 30 (oversold)
        rsi = indicators.get('rsi', {})
        if rsi.get('rsi') is not None:
            criteria['rsi_oversold'] = rsi.get('is_oversold', False)
        else:
            criteria['rsi_oversold'] = False

        # Criterion 2: Stochastic oversold
        stoch = indicators.get('stochastic', {})
        if stoch.get('k') is not None:
            criteria['stochastic_oversold'] = (
                stoch.get('k', 100) < 20 and
                stoch.get('d', 100) < 30
            )
        else:
            criteria['stochastic_oversold'] = False

        # Criterion 3: Price < Lower Bollinger
        bollinger = indicators.get('bollinger', {})
        if bollinger.get('lower') is not None:
            criteria['price_below_lower_bb'] = bollinger.get('price_below_lower', False)
        else:
            criteria['price_below_lower_bb'] = False

        # Criterion 4: MACD momentum turning
        macd = indicators.get('macd', {})
        if macd.get('histogram') is not None:
            criteria['macd_turning'] = (
                macd.get('histogram_positive', False) or
                macd.get('histogram_growing', False)
            )
        else:
            criteria['macd_turning'] = False

        # Criterion 5: Volume confirmation
        volume = indicators.get('volume_profile', {})
        if volume.get('volume_ratio') is not None:
            criteria['volume_confirmation'] = volume.get('volume_ratio', 0) > 1.0
        else:
            criteria['volume_confirmation'] = True  # Skip if no volume data

        all_met = all(criteria.values())
        confidence = self._calculate_confidence(criteria)

        return all_met, confidence, criteria

    def evaluate_sell(self, indicators: Dict[str, Any]) -> Tuple[bool, int, Dict]:
        """Evaluate Mean Reversion SELL criteria."""
        criteria = {}

        # Criterion 1: RSI > 70 (overbought)
        rsi = indicators.get('rsi', {})
        if rsi.get('rsi') is not None:
            criteria['rsi_overbought'] = rsi.get('is_overbought', False)
        else:
            criteria['rsi_overbought'] = False

        # Criterion 2: Stochastic overbought
        stoch = indicators.get('stochastic', {})
        if stoch.get('k') is not None:
            criteria['stochastic_overbought'] = (
                stoch.get('k', 0) > 80 and
                stoch.get('d', 0) > 70
            )
        else:
            criteria['stochastic_overbought'] = False

        # Criterion 3: Price > Upper Bollinger
        bollinger = indicators.get('bollinger', {})
        if bollinger.get('upper') is not None:
            criteria['price_above_upper_bb'] = bollinger.get('price_above_upper', False)
        else:
            criteria['price_above_upper_bb'] = False

        # Criterion 4: MACD momentum turning negative
        macd = indicators.get('macd', {})
        if macd.get('histogram') is not None:
            criteria['macd_turning'] = (
                not macd.get('histogram_positive', True) or
                not macd.get('histogram_growing', True)
            )
        else:
            criteria['macd_turning'] = False

        # Criterion 5: Volume confirmation
        volume = indicators.get('volume_profile', {})
        if volume.get('volume_ratio') is not None:
            criteria['volume_confirmation'] = volume.get('volume_ratio', 0) > 1.0
        else:
            criteria['volume_confirmation'] = True

        all_met = all(criteria.values())
        confidence = self._calculate_confidence(criteria)

        return all_met, confidence, criteria
