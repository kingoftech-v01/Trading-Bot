"""
Golden Confluence - Combination 1.

Win Rate: 62%, Risk/Reward: 3.8:1

Indicators:
- RSI(14)
- MACD(12,26,9)
- ADX(14)
- Stochastic(14,3,3)
- Bollinger Bands(20,2)

BUY Criteria:
1. RSI > 50 AND RSI ascending from < 30 zone
2. MACD Line > Signal Line AND Histogram > 0 and growing
3. ADX > 25 AND +DI > -DI
4. Stochastic: K% > D% with K% < 80
5. Price > Lower Bollinger Band AND bounce visible
"""

from typing import Dict, Any, List, Tuple
from .base_combination import BaseCombination


class GoldenConfluence(BaseCombination):
    """
    THE GOLDEN CONFLUENCE

    Best for: Trending markets with established direction.
    Frequency: ~127 trades/year
    """

    def get_name(self) -> str:
        return 'golden_confluence'

    def get_display_name(self) -> str:
        return 'Golden Confluence'

    def get_win_rate(self) -> float:
        return 62.0

    def get_risk_reward_ratio(self) -> float:
        return 3.8

    def get_required_indicators(self) -> List[str]:
        return ['rsi', 'macd', 'adx', 'stochastic', 'bollinger']

    def evaluate_buy(self, indicators: Dict[str, Any]) -> Tuple[bool, int, Dict]:
        """Evaluate Golden Confluence BUY criteria."""
        criteria = {}

        # Criterion 1: RSI
        rsi = indicators.get('rsi', {})
        rsi_value = rsi.get('rsi')
        prev_rsi = rsi.get('previous_rsi')

        if rsi_value is not None and prev_rsi is not None:
            # RSI > 50 and ascending from oversold zone
            criteria['rsi_bullish'] = rsi_value > 50 and prev_rsi < 30
        else:
            criteria['rsi_bullish'] = False

        # Criterion 2: MACD
        macd = indicators.get('macd', {})
        if macd.get('macd_line') is not None:
            criteria['macd_bullish'] = (
                macd.get('is_bullish', False) and
                macd.get('histogram_positive', False) and
                macd.get('histogram_growing', False)
            )
        else:
            criteria['macd_bullish'] = False

        # Criterion 3: ADX
        adx = indicators.get('adx', {})
        if adx.get('adx') is not None:
            criteria['adx_trending'] = (
                adx.get('is_trending', False) and
                adx.get('is_bullish_trend', False)
            )
        else:
            criteria['adx_trending'] = False

        # Criterion 4: Stochastic
        stoch = indicators.get('stochastic', {})
        if stoch.get('k') is not None:
            criteria['stochastic_bullish'] = (
                stoch.get('k_above_d', False) and
                not stoch.get('is_overbought', True)
            )
        else:
            criteria['stochastic_bullish'] = False

        # Criterion 5: Bollinger Bands
        bollinger = indicators.get('bollinger', {})
        if bollinger.get('lower') is not None:
            current_close = indicators.get('current_close', 0)
            lower = bollinger.get('lower', 0)
            middle = bollinger.get('middle', 0)

            # Price above lower band, bouncing (below middle)
            criteria['bollinger_bounce'] = (
                current_close > lower and
                current_close < middle
            )
        else:
            criteria['bollinger_bounce'] = False

        # All criteria must be met
        all_met = all(criteria.values())
        confidence = self._calculate_confidence(criteria)

        return all_met, confidence, criteria

    def evaluate_sell(self, indicators: Dict[str, Any]) -> Tuple[bool, int, Dict]:
        """Evaluate Golden Confluence SELL criteria (inverse of buy)."""
        criteria = {}

        # Criterion 1: RSI
        rsi = indicators.get('rsi', {})
        rsi_value = rsi.get('rsi')
        prev_rsi = rsi.get('previous_rsi')

        if rsi_value is not None and prev_rsi is not None:
            # RSI < 50 and descending from overbought zone
            criteria['rsi_bearish'] = rsi_value < 50 and prev_rsi > 70
        else:
            criteria['rsi_bearish'] = False

        # Criterion 2: MACD
        macd = indicators.get('macd', {})
        if macd.get('macd_line') is not None:
            criteria['macd_bearish'] = (
                not macd.get('is_bullish', True) and
                not macd.get('histogram_positive', True) and
                not macd.get('histogram_growing', True)
            )
        else:
            criteria['macd_bearish'] = False

        # Criterion 3: ADX
        adx = indicators.get('adx', {})
        if adx.get('adx') is not None:
            criteria['adx_trending'] = (
                adx.get('is_trending', False) and
                adx.get('is_bearish_trend', False)
            )
        else:
            criteria['adx_trending'] = False

        # Criterion 4: Stochastic
        stoch = indicators.get('stochastic', {})
        if stoch.get('k') is not None:
            criteria['stochastic_bearish'] = (
                not stoch.get('k_above_d', True) and
                not stoch.get('is_oversold', True)
            )
        else:
            criteria['stochastic_bearish'] = False

        # Criterion 5: Bollinger Bands
        bollinger = indicators.get('bollinger', {})
        if bollinger.get('upper') is not None:
            current_close = indicators.get('current_close', 0)
            upper = bollinger.get('upper', 0)
            middle = bollinger.get('middle', 0)

            # Price below upper band, falling (above middle)
            criteria['bollinger_rejection'] = (
                current_close < upper and
                current_close > middle
            )
        else:
            criteria['bollinger_rejection'] = False

        all_met = all(criteria.values())
        confidence = self._calculate_confidence(criteria)

        return all_met, confidence, criteria
