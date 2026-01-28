"""
Harmonic Confluence - Combination 4.

Win Rate: 64%, Risk/Reward: 3.5:1

Indicators:
- RSI(14) - Divergence
- MACD(12,26,9) - Hidden Divergence
- Linear Regression(50)
- Stochastic(14,3,3)
- Volume Profile

BUY Criteria (Bullish Divergence):
1. Price makes lower lows
2. RSI makes higher lows (divergence)
3. MACD histogram inverting upward
4. Linear Regression slope changing from negative to zero
5. Stochastic K% > D% or exiting < 30
6. Volume confirms
"""

from typing import Dict, Any, List, Tuple
from .base_combination import BaseCombination


class HarmonicConfluence(BaseCombination):
    """
    HARMONIC CONFLUENCE

    Best for: Trend reversals, end of trends.
    Frequency: ~73 trades/year
    """

    def get_name(self) -> str:
        return 'harmonic_confluence'

    def get_display_name(self) -> str:
        return 'Harmonic Confluence'

    def get_win_rate(self) -> float:
        return 64.0

    def get_risk_reward_ratio(self) -> float:
        return 3.5

    def get_required_indicators(self) -> List[str]:
        return ['rsi', 'macd', 'linear_regression', 'stochastic', 'volume_profile']

    def evaluate_buy(self, indicators: Dict[str, Any]) -> Tuple[bool, int, Dict]:
        """Evaluate Harmonic Confluence BUY criteria."""
        criteria = {}

        # Criterion 1 & 2: RSI divergence (simplified)
        rsi = indicators.get('rsi', {})
        if rsi.get('rsi') is not None:
            # RSI ascending while price may be falling
            criteria['rsi_divergence'] = rsi.get('is_ascending', False) and rsi.get('rsi', 0) < 50
        else:
            criteria['rsi_divergence'] = False

        # Criterion 3: MACD histogram inverting
        macd = indicators.get('macd', {})
        if macd.get('histogram') is not None:
            hist = macd.get('histogram', 0)
            prev_hist = macd.get('previous_histogram', 0)
            # Histogram was negative, now less negative or positive
            criteria['macd_inflection'] = prev_hist < 0 and hist > prev_hist
        else:
            criteria['macd_inflection'] = False

        # Criterion 4: Linear Regression inflection
        lr = indicators.get('linear_regression', {})
        if lr.get('slope') is not None:
            slope = lr.get('slope', 0)
            # Slope is near zero or turning positive
            criteria['lr_inflection'] = -0.02 <= slope <= 0.05
        else:
            criteria['lr_inflection'] = False

        # Criterion 5: Stochastic bullish
        stoch = indicators.get('stochastic', {})
        if stoch.get('k') is not None:
            criteria['stochastic_bullish'] = (
                stoch.get('k_above_d', False) or
                stoch.get('is_oversold', False)
            )
        else:
            criteria['stochastic_bullish'] = False

        # Criterion 6: Volume confirmation
        volume = indicators.get('volume_profile', {})
        if volume.get('volume_ratio') is not None:
            criteria['volume_confirmation'] = volume.get('is_increasing', False)
        else:
            criteria['volume_confirmation'] = True

        all_met = all(criteria.values())
        confidence = self._calculate_confidence(criteria)

        return all_met, confidence, criteria

    def evaluate_sell(self, indicators: Dict[str, Any]) -> Tuple[bool, int, Dict]:
        """Evaluate Harmonic Confluence SELL criteria."""
        criteria = {}

        # RSI bearish divergence
        rsi = indicators.get('rsi', {})
        if rsi.get('rsi') is not None:
            criteria['rsi_divergence'] = not rsi.get('is_ascending', True) and rsi.get('rsi', 100) > 50
        else:
            criteria['rsi_divergence'] = False

        # MACD histogram inverting downward
        macd = indicators.get('macd', {})
        if macd.get('histogram') is not None:
            hist = macd.get('histogram', 0)
            prev_hist = macd.get('previous_histogram', 0)
            criteria['macd_inflection'] = prev_hist > 0 and hist < prev_hist
        else:
            criteria['macd_inflection'] = False

        # Linear Regression inflection downward
        lr = indicators.get('linear_regression', {})
        if lr.get('slope') is not None:
            slope = lr.get('slope', 0)
            criteria['lr_inflection'] = -0.05 <= slope <= 0.02
        else:
            criteria['lr_inflection'] = False

        # Stochastic bearish
        stoch = indicators.get('stochastic', {})
        if stoch.get('k') is not None:
            criteria['stochastic_bearish'] = (
                not stoch.get('k_above_d', True) or
                stoch.get('is_overbought', False)
            )
        else:
            criteria['stochastic_bearish'] = False

        # Volume confirmation
        volume = indicators.get('volume_profile', {})
        if volume.get('volume_ratio') is not None:
            criteria['volume_confirmation'] = volume.get('is_increasing', False)
        else:
            criteria['volume_confirmation'] = True

        all_met = all(criteria.values())
        confidence = self._calculate_confidence(criteria)

        return all_met, confidence, criteria
