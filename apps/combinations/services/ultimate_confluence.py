"""
The Ultimate Confluence - Combination 8.

Win Rate: 58%, Risk/Reward: 4.5:1

Indicators (ALL 8+ required):
- RSI(14)
- MACD(12,26,9)
- ADX(14)
- Stochastic(14,3,3)
- Bollinger Bands(20,2)
- Linear Regression(50)
- Volume Profile
- CCI(20)
- ATR(14)

BUY Criteria (ALL must be met):
1. RSI > 50
2. MACD Histogram > 0 and growing
3. ADX > 25 with +DI > -DI
4. Stochastic K% > D%
5. Price > Lower BB
6. LR slope > 0.02 AND r² > 0.60
7. Volume > average
8. CCI > 0 and rising
"""

from typing import Dict, Any, List, Tuple
from .base_combination import BaseCombination


class UltimateConfluence(BaseCombination):
    """
    THE ULTIMATE CONFLUENCE

    Best for: Maximum confidence trades, rare but highly profitable.
    Frequency: ~12 trades/year (lowest)
    """

    def get_name(self) -> str:
        return 'ultimate_confluence'

    def get_display_name(self) -> str:
        return 'The Ultimate Confluence'

    def get_win_rate(self) -> float:
        return 58.0

    def get_risk_reward_ratio(self) -> float:
        return 4.5

    def get_required_indicators(self) -> List[str]:
        return [
            'rsi', 'macd', 'adx', 'stochastic', 'bollinger',
            'linear_regression', 'volume_profile', 'cci', 'atr'
        ]

    def evaluate_buy(self, indicators: Dict[str, Any]) -> Tuple[bool, int, Dict]:
        """Evaluate Ultimate Confluence BUY criteria."""
        criteria = {}

        # 1. RSI > 50
        rsi = indicators.get('rsi', {})
        if rsi.get('rsi') is not None:
            criteria['rsi_bullish'] = rsi.get('rsi', 0) > 50
        else:
            criteria['rsi_bullish'] = False

        # 2. MACD Histogram > 0 and growing
        macd = indicators.get('macd', {})
        if macd.get('histogram') is not None:
            criteria['macd_bullish'] = (
                macd.get('histogram_positive', False) and
                macd.get('histogram_growing', False)
            )
        else:
            criteria['macd_bullish'] = False

        # 3. ADX > 25 with +DI > -DI
        adx = indicators.get('adx', {})
        if adx.get('adx') is not None:
            criteria['adx_bullish'] = (
                adx.get('is_trending', False) and
                adx.get('is_bullish_trend', False)
            )
        else:
            criteria['adx_bullish'] = False

        # 4. Stochastic K% > D%
        stoch = indicators.get('stochastic', {})
        if stoch.get('k') is not None:
            criteria['stoch_bullish'] = stoch.get('k_above_d', False)
        else:
            criteria['stoch_bullish'] = False

        # 5. Price > Lower BB
        bollinger = indicators.get('bollinger', {})
        if bollinger.get('lower') is not None:
            current_close = indicators.get('current_close', 0)
            criteria['bollinger_ok'] = current_close > bollinger.get('lower', 0)
        else:
            criteria['bollinger_ok'] = False

        # 6. LR slope > 0.02 AND r² > 0.60
        lr = indicators.get('linear_regression', {})
        if lr.get('slope') is not None:
            criteria['lr_bullish'] = (
                lr.get('is_uptrend', False) and
                lr.get('is_clear_trend', False)
            )
        else:
            criteria['lr_bullish'] = False

        # 7. Volume > average
        volume = indicators.get('volume_profile', {})
        if volume.get('volume_ratio') is not None:
            criteria['volume_ok'] = volume.get('volume_ratio', 0) > 1.0
        else:
            criteria['volume_ok'] = False

        # 8. CCI > 0 and rising
        cci = indicators.get('cci', {})
        if cci.get('cci') is not None:
            criteria['cci_bullish'] = (
                cci.get('is_positive', False) and
                cci.get('is_rising', False)
            )
        else:
            criteria['cci_bullish'] = False

        all_met = all(criteria.values())
        confidence = self._calculate_confidence(criteria)

        return all_met, confidence, criteria

    def evaluate_sell(self, indicators: Dict[str, Any]) -> Tuple[bool, int, Dict]:
        """Evaluate Ultimate Confluence SELL criteria."""
        criteria = {}

        # 1. RSI < 50
        rsi = indicators.get('rsi', {})
        if rsi.get('rsi') is not None:
            criteria['rsi_bearish'] = rsi.get('rsi', 100) < 50
        else:
            criteria['rsi_bearish'] = False

        # 2. MACD Histogram < 0 and falling
        macd = indicators.get('macd', {})
        if macd.get('histogram') is not None:
            criteria['macd_bearish'] = (
                not macd.get('histogram_positive', True) and
                not macd.get('histogram_growing', True)
            )
        else:
            criteria['macd_bearish'] = False

        # 3. ADX > 25 with -DI > +DI
        adx = indicators.get('adx', {})
        if adx.get('adx') is not None:
            criteria['adx_bearish'] = (
                adx.get('is_trending', False) and
                adx.get('is_bearish_trend', False)
            )
        else:
            criteria['adx_bearish'] = False

        # 4. Stochastic K% < D%
        stoch = indicators.get('stochastic', {})
        if stoch.get('k') is not None:
            criteria['stoch_bearish'] = not stoch.get('k_above_d', True)
        else:
            criteria['stoch_bearish'] = False

        # 5. Price < Upper BB
        bollinger = indicators.get('bollinger', {})
        if bollinger.get('upper') is not None:
            current_close = indicators.get('current_close', float('inf'))
            criteria['bollinger_ok'] = current_close < bollinger.get('upper', float('inf'))
        else:
            criteria['bollinger_ok'] = False

        # 6. LR slope < -0.02 AND r² > 0.60
        lr = indicators.get('linear_regression', {})
        if lr.get('slope') is not None:
            criteria['lr_bearish'] = (
                lr.get('is_downtrend', False) and
                lr.get('is_clear_trend', False)
            )
        else:
            criteria['lr_bearish'] = False

        # 7. Volume > average
        volume = indicators.get('volume_profile', {})
        if volume.get('volume_ratio') is not None:
            criteria['volume_ok'] = volume.get('volume_ratio', 0) > 1.0
        else:
            criteria['volume_ok'] = False

        # 8. CCI < 0 and falling
        cci = indicators.get('cci', {})
        if cci.get('cci') is not None:
            criteria['cci_bearish'] = (
                not cci.get('is_positive', True) and
                not cci.get('is_rising', True)
            )
        else:
            criteria['cci_bearish'] = False

        all_met = all(criteria.values())
        confidence = self._calculate_confidence(criteria)

        return all_met, confidence, criteria
