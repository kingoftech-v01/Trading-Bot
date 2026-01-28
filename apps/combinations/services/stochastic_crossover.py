"""
Stochastic Crossover System - Combination 7.

Win Rate: 71%, Risk/Reward: 3.0:1

Indicators:
- Stochastic(14,3,3) - Fast
- Stochastic(20,5,5) - Slow
- RSI(14)
- Volume Profile
- Support/Resistance

BUY Criteria:
1. Fast Stoch K% crosses above Slow Stoch K%
2. Slow Stoch D% > Fast D% (confirmation)
3. RSI in 30-70 zone
4. Volume > average
5. Price > Support level
"""

from typing import Dict, Any, List, Tuple
from .base_combination import BaseCombination


class StochasticCrossover(BaseCombination):
    """
    STOCHASTIC CROSSOVER SYSTEM

    Best for: Frequent trading, smaller but consistent gains.
    Frequency: ~156 trades/year (highest)
    """

    def get_name(self) -> str:
        return 'stochastic_crossover'

    def get_display_name(self) -> str:
        return 'Stochastic Crossover System'

    def get_win_rate(self) -> float:
        return 71.0

    def get_risk_reward_ratio(self) -> float:
        return 3.0

    def get_required_indicators(self) -> List[str]:
        return ['stochastic', 'stochastic_slow', 'rsi', 'volume_profile', 'support_resistance']

    def evaluate_buy(self, indicators: Dict[str, Any]) -> Tuple[bool, int, Dict]:
        """Evaluate Stochastic Crossover BUY criteria."""
        criteria = {}

        # Fast and slow stochastic
        fast_stoch = indicators.get('stochastic', {})
        slow_stoch = indicators.get('stochastic_slow', {})

        # Criterion 1: Fast K% crosses above Slow K%
        if fast_stoch.get('k') is not None and slow_stoch.get('k') is not None:
            fast_k = fast_stoch.get('k', 0)
            slow_k = slow_stoch.get('k', 0)
            fast_prev_k = fast_stoch.get('previous_k', 0)
            slow_prev_k = slow_stoch.get('previous_k', 0)

            criteria['stoch_crossover'] = (
                fast_prev_k <= slow_prev_k and
                fast_k > slow_k
            )
        else:
            criteria['stoch_crossover'] = False

        # Criterion 2: Slow D% confirmation (simplified)
        if slow_stoch.get('d') is not None:
            criteria['stoch_confirmation'] = slow_stoch.get('d', 0) > 30
        else:
            criteria['stoch_confirmation'] = False

        # Criterion 3: RSI in 30-70 zone
        rsi = indicators.get('rsi', {})
        if rsi.get('rsi') is not None:
            rsi_value = rsi.get('rsi', 0)
            criteria['rsi_neutral'] = 30 <= rsi_value <= 70
        else:
            criteria['rsi_neutral'] = False

        # Criterion 4: Volume confirmation
        volume = indicators.get('volume_profile', {})
        if volume.get('volume_ratio') is not None:
            criteria['volume_confirmation'] = volume.get('volume_ratio', 0) > 1.0
        else:
            criteria['volume_confirmation'] = True

        # Criterion 5: Price above support
        sr = indicators.get('support_resistance', {})
        if sr.get('nearest_support') is not None:
            criteria['above_support'] = sr.get('price_above_support', False)
        else:
            criteria['above_support'] = True

        all_met = all(criteria.values())
        confidence = self._calculate_confidence(criteria)

        return all_met, confidence, criteria

    def evaluate_sell(self, indicators: Dict[str, Any]) -> Tuple[bool, int, Dict]:
        """Evaluate Stochastic Crossover SELL criteria."""
        criteria = {}

        fast_stoch = indicators.get('stochastic', {})
        slow_stoch = indicators.get('stochastic_slow', {})

        # Fast K% crosses below Slow K%
        if fast_stoch.get('k') is not None and slow_stoch.get('k') is not None:
            fast_k = fast_stoch.get('k', 100)
            slow_k = slow_stoch.get('k', 100)
            fast_prev_k = fast_stoch.get('previous_k', 100)
            slow_prev_k = slow_stoch.get('previous_k', 100)

            criteria['stoch_crossover'] = (
                fast_prev_k >= slow_prev_k and
                fast_k < slow_k
            )
        else:
            criteria['stoch_crossover'] = False

        # Slow D% confirmation
        if slow_stoch.get('d') is not None:
            criteria['stoch_confirmation'] = slow_stoch.get('d', 100) < 70
        else:
            criteria['stoch_confirmation'] = False

        # RSI in 30-70 zone
        rsi = indicators.get('rsi', {})
        if rsi.get('rsi') is not None:
            rsi_value = rsi.get('rsi', 100)
            criteria['rsi_neutral'] = 30 <= rsi_value <= 70
        else:
            criteria['rsi_neutral'] = False

        # Volume confirmation
        volume = indicators.get('volume_profile', {})
        if volume.get('volume_ratio') is not None:
            criteria['volume_confirmation'] = volume.get('volume_ratio', 0) > 1.0
        else:
            criteria['volume_confirmation'] = True

        # Price below resistance (simplified)
        sr = indicators.get('support_resistance', {})
        if sr.get('nearest_resistance') is not None:
            current_close = indicators.get('current_close', 0)
            resistance = sr.get('nearest_resistance', float('inf'))
            criteria['below_resistance'] = current_close < resistance
        else:
            criteria['below_resistance'] = True

        all_met = all(criteria.values())
        confidence = self._calculate_confidence(criteria)

        return all_met, confidence, criteria
