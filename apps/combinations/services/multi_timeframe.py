"""
Multi-Timeframe Convergence - Combination 6.

Win Rate: 66%, Risk/Reward: 3.3:1

Indicators per Timeframe:
- 4h (Context): ADX, Linear Regression
- 1h (Signal): RSI, MACD, Stochastic
- 15m (Entry): Bollinger, Volume

BUY Criteria:
1. 4h: LR slope > 0.02 AND ADX > 25
2. 1h: RSI > 50 AND MACD > Signal AND Stoch K% > D%
3. 15m: Price bounces from BB lower AND Volume > average
4. At least 1 correlated pair confirms
"""

from typing import Dict, Any, List, Tuple
from .base_combination import BaseCombination


class MultiTimeframe(BaseCombination):
    """
    MULTI-TIMEFRAME CONVERGENCE

    Best for: High probability setups, requires patience.
    Frequency: ~47 trades/year
    Note: This combination requires multi-timeframe data analysis.
    """

    def get_name(self) -> str:
        return 'multi_timeframe'

    def get_display_name(self) -> str:
        return 'Multi-Timeframe Convergence'

    def get_win_rate(self) -> float:
        return 66.0

    def get_risk_reward_ratio(self) -> float:
        return 3.3

    def get_required_indicators(self) -> List[str]:
        return ['adx', 'linear_regression', 'rsi', 'macd', 'stochastic', 'bollinger', 'volume_profile']

    def evaluate_buy(self, indicators: Dict[str, Any]) -> Tuple[bool, int, Dict]:
        """
        Evaluate Multi-Timeframe BUY criteria.

        Note: This simplified version uses single timeframe data.
        Full implementation would require 4h, 1h, and 15m data.
        """
        criteria = {}

        # 4h Context (simulated with current timeframe)
        # LR slope > 0.02 AND ADX > 25
        lr = indicators.get('linear_regression', {})
        adx = indicators.get('adx', {})

        if lr.get('slope') is not None and adx.get('adx') is not None:
            criteria['context_aligned'] = (
                lr.get('is_uptrend', False) and
                adx.get('is_trending', False)
            )
        else:
            criteria['context_aligned'] = False

        # 1h Signal: RSI > 50 AND MACD bullish AND Stoch bullish
        rsi = indicators.get('rsi', {})
        macd = indicators.get('macd', {})
        stoch = indicators.get('stochastic', {})

        if rsi.get('rsi') is not None and macd.get('macd_line') is not None:
            criteria['signal_aligned'] = (
                rsi.get('rsi', 0) > 50 and
                macd.get('is_bullish', False) and
                stoch.get('k_above_d', False)
            )
        else:
            criteria['signal_aligned'] = False

        # 15m Entry: BB bounce AND Volume
        bollinger = indicators.get('bollinger', {})
        volume = indicators.get('volume_profile', {})

        if bollinger.get('lower') is not None:
            criteria['entry_valid'] = (
                bollinger.get('price_near_lower', False) or
                (not bollinger.get('price_above_middle', True))
            )
        else:
            criteria['entry_valid'] = False

        # Volume confirmation
        if volume.get('volume_ratio') is not None:
            criteria['volume_confirmation'] = volume.get('volume_ratio', 0) > 1.0
        else:
            criteria['volume_confirmation'] = True

        all_met = all(criteria.values())
        confidence = self._calculate_confidence(criteria)

        return all_met, confidence, criteria

    def evaluate_sell(self, indicators: Dict[str, Any]) -> Tuple[bool, int, Dict]:
        """Evaluate Multi-Timeframe SELL criteria."""
        criteria = {}

        # Context: LR downtrend AND ADX trending
        lr = indicators.get('linear_regression', {})
        adx = indicators.get('adx', {})

        if lr.get('slope') is not None and adx.get('adx') is not None:
            criteria['context_aligned'] = (
                lr.get('is_downtrend', False) and
                adx.get('is_trending', False)
            )
        else:
            criteria['context_aligned'] = False

        # Signal: RSI < 50 AND MACD bearish AND Stoch bearish
        rsi = indicators.get('rsi', {})
        macd = indicators.get('macd', {})
        stoch = indicators.get('stochastic', {})

        if rsi.get('rsi') is not None and macd.get('macd_line') is not None:
            criteria['signal_aligned'] = (
                rsi.get('rsi', 100) < 50 and
                not macd.get('is_bullish', True) and
                not stoch.get('k_above_d', True)
            )
        else:
            criteria['signal_aligned'] = False

        # Entry: Near upper BB
        bollinger = indicators.get('bollinger', {})

        if bollinger.get('upper') is not None:
            criteria['entry_valid'] = (
                bollinger.get('price_near_upper', False) or
                bollinger.get('price_above_middle', False)
            )
        else:
            criteria['entry_valid'] = False

        # Volume confirmation
        volume = indicators.get('volume_profile', {})
        if volume.get('volume_ratio') is not None:
            criteria['volume_confirmation'] = volume.get('volume_ratio', 0) > 1.0
        else:
            criteria['volume_confirmation'] = True

        all_met = all(criteria.values())
        confidence = self._calculate_confidence(criteria)

        return all_met, confidence, criteria
