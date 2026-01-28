"""
Take Profit Calculator - Determines optimal take profit levels.

Provides multiple methods for take profit placement:
- Risk/Reward based
- Resistance/Support based
- ATR-based
- Fibonacci extensions
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
import logging

from apps.core.services.base_service import BaseService, ServiceResult


logger = logging.getLogger('trading_bot')


class TakeProfitCalculator(BaseService):
    """
    Calculates take profit levels using various methods.

    Methods:
    1. Risk/Reward: Based on target R:R ratio
    2. Resistance/Support: Based on key levels
    3. ATR-based: Multiple of ATR
    4. Fibonacci: Extension levels
    """

    # Default settings
    DEFAULT_RISK_REWARD = 3.0
    DEFAULT_ATR_MULTIPLIER = 4.0

    def calculate_risk_reward_based(
        self,
        entry_price: Decimal,
        stop_loss: Decimal,
        direction: str = 'buy',
        risk_reward: float = None,
    ) -> ServiceResult:
        """
        Calculate take profit based on risk/reward ratio.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            direction: 'buy' or 'sell'
            risk_reward: Target R:R ratio (default: 3.0)

        Returns:
            ServiceResult with take profit data
        """
        try:
            entry_price = Decimal(str(entry_price))
            stop_loss = Decimal(str(stop_loss))
            risk_reward = Decimal(str(risk_reward or self.DEFAULT_RISK_REWARD))

            # Calculate risk distance
            if direction == 'buy':
                risk_distance = entry_price - stop_loss
                take_profit = entry_price + (risk_distance * risk_reward)
            else:
                risk_distance = stop_loss - entry_price
                take_profit = entry_price - (risk_distance * risk_reward)

            reward_distance = abs(take_profit - entry_price)
            tp_percent = (reward_distance / entry_price) * 100

            return self.success_result({
                'take_profit': float(take_profit),
                'entry_price': float(entry_price),
                'stop_loss': float(stop_loss),
                'risk_distance': float(risk_distance),
                'reward_distance': float(reward_distance),
                'tp_percent': float(tp_percent),
                'risk_reward': float(risk_reward),
                'method': 'risk_reward',
                'direction': direction,
            })

        except Exception as e:
            self.log_error(f"Error calculating R:R TP: {str(e)}", exc=e)
            return self.error_result(str(e))

    def calculate_resistance_support_based(
        self,
        entry_price: Decimal,
        direction: str = 'buy',
        resistance: Decimal = None,
        support: Decimal = None,
        buffer_percent: float = 0.001,
    ) -> ServiceResult:
        """
        Calculate take profit based on support/resistance.

        Args:
            entry_price: Entry price
            direction: 'buy' or 'sell'
            resistance: Resistance level (for buys)
            support: Support level (for sells)
            buffer_percent: Buffer before level

        Returns:
            ServiceResult with take profit data
        """
        try:
            entry_price = Decimal(str(entry_price))
            buffer_percent = Decimal(str(buffer_percent))

            if direction == 'buy':
                if resistance is None:
                    return self.error_result(
                        "Resistance level required for buy orders"
                    )

                resistance = Decimal(str(resistance))
                buffer = resistance * buffer_percent
                take_profit = resistance - buffer

            else:  # sell
                if support is None:
                    return self.error_result(
                        "Support level required for sell orders"
                    )

                support = Decimal(str(support))
                buffer = support * buffer_percent
                take_profit = support + buffer

            reward_distance = abs(take_profit - entry_price)
            tp_percent = (reward_distance / entry_price) * 100

            return self.success_result({
                'take_profit': float(take_profit),
                'entry_price': float(entry_price),
                'reward_distance': float(reward_distance),
                'tp_percent': float(tp_percent),
                'resistance': float(resistance) if resistance else None,
                'support': float(support) if support else None,
                'buffer_percent': float(buffer_percent * 100),
                'method': 'support_resistance',
                'direction': direction,
            })

        except Exception as e:
            self.log_error(f"Error calculating S/R TP: {str(e)}", exc=e)
            return self.error_result(str(e))

    def calculate_atr_based(
        self,
        entry_price: Decimal,
        atr: Decimal,
        direction: str = 'buy',
        multiplier: float = None,
    ) -> ServiceResult:
        """
        Calculate ATR-based take profit.

        Args:
            entry_price: Entry price
            atr: Average True Range value
            direction: 'buy' or 'sell'
            multiplier: ATR multiplier (default: 4.0)

        Returns:
            ServiceResult with take profit data
        """
        try:
            entry_price = Decimal(str(entry_price))
            atr = Decimal(str(atr))
            multiplier = Decimal(str(multiplier or self.DEFAULT_ATR_MULTIPLIER))

            reward_distance = atr * multiplier

            if direction == 'buy':
                take_profit = entry_price + reward_distance
            else:
                take_profit = entry_price - reward_distance

            tp_percent = (reward_distance / entry_price) * 100

            return self.success_result({
                'take_profit': float(take_profit),
                'entry_price': float(entry_price),
                'reward_distance': float(reward_distance),
                'tp_percent': float(tp_percent),
                'atr': float(atr),
                'multiplier': float(multiplier),
                'method': 'atr',
                'direction': direction,
            })

        except Exception as e:
            self.log_error(f"Error calculating ATR TP: {str(e)}", exc=e)
            return self.error_result(str(e))

    def calculate_fibonacci_targets(
        self,
        entry_price: Decimal,
        swing_low: Decimal,
        swing_high: Decimal,
        direction: str = 'buy',
    ) -> ServiceResult:
        """
        Calculate Fibonacci extension take profit levels.

        Args:
            entry_price: Entry price
            swing_low: Recent swing low
            swing_high: Recent swing high
            direction: 'buy' or 'sell'

        Returns:
            ServiceResult with Fibonacci levels
        """
        try:
            entry_price = Decimal(str(entry_price))
            swing_low = Decimal(str(swing_low))
            swing_high = Decimal(str(swing_high))

            swing_range = swing_high - swing_low

            # Fibonacci extension levels
            fib_levels = {
                '1.0': Decimal('1.0'),
                '1.272': Decimal('1.272'),
                '1.618': Decimal('1.618'),
                '2.0': Decimal('2.0'),
                '2.618': Decimal('2.618'),
            }

            targets = {}
            if direction == 'buy':
                for name, level in fib_levels.items():
                    targets[name] = float(swing_high + (swing_range * (level - 1)))
            else:
                for name, level in fib_levels.items():
                    targets[name] = float(swing_low - (swing_range * (level - 1)))

            # Primary target is 1.618 extension
            primary_target = targets['1.618']

            return self.success_result({
                'take_profit': primary_target,
                'fibonacci_targets': targets,
                'entry_price': float(entry_price),
                'swing_low': float(swing_low),
                'swing_high': float(swing_high),
                'swing_range': float(swing_range),
                'method': 'fibonacci',
                'direction': direction,
            })

        except Exception as e:
            self.log_error(f"Error calculating Fib TP: {str(e)}", exc=e)
            return self.error_result(str(e))

    def calculate_multiple_targets(
        self,
        entry_price: Decimal,
        stop_loss: Decimal,
        direction: str = 'buy',
        targets: List[float] = None,
    ) -> ServiceResult:
        """
        Calculate multiple take profit targets for scaling out.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            direction: 'buy' or 'sell'
            targets: List of R:R ratios for each target

        Returns:
            ServiceResult with multiple targets
        """
        try:
            entry_price = Decimal(str(entry_price))
            stop_loss = Decimal(str(stop_loss))
            targets = targets or [1.5, 2.0, 3.0]

            # Calculate risk distance
            if direction == 'buy':
                risk_distance = entry_price - stop_loss
            else:
                risk_distance = stop_loss - entry_price

            take_profit_levels = []
            for i, rr in enumerate(targets):
                rr = Decimal(str(rr))
                if direction == 'buy':
                    tp = entry_price + (risk_distance * rr)
                else:
                    tp = entry_price - (risk_distance * rr)

                take_profit_levels.append({
                    'level': i + 1,
                    'take_profit': float(tp),
                    'risk_reward': float(rr),
                    'tp_percent': float((abs(tp - entry_price) / entry_price) * 100),
                })

            return self.success_result({
                'take_profit_levels': take_profit_levels,
                'primary_take_profit': take_profit_levels[-1]['take_profit'],
                'entry_price': float(entry_price),
                'stop_loss': float(stop_loss),
                'risk_distance': float(risk_distance),
                'method': 'multiple_targets',
                'direction': direction,
            })

        except Exception as e:
            self.log_error(f"Error calculating multiple TPs: {str(e)}", exc=e)
            return self.error_result(str(e))
