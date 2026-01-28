"""
Position Sizer - Calculates optimal position sizes.

Uses risk-based position sizing to determine the correct
position size based on account balance and risk parameters.
"""

from typing import Dict, Any, Optional
from decimal import Decimal, ROUND_DOWN
import logging

from apps.core.services.base_service import BaseService, ServiceResult
from ..models import RiskProfile, PositionSizeCalculation


logger = logging.getLogger('trading_bot')


class PositionSizer(BaseService):
    """
    Calculates position sizes based on risk parameters.

    Position sizing formula:
    Position Size = Risk Amount / (Entry Price - Stop Loss)

    For shorts:
    Position Size = Risk Amount / (Stop Loss - Entry Price)
    """

    def __init__(self, risk_profile: RiskProfile = None):
        """
        Initialize position sizer.

        Args:
            risk_profile: RiskProfile to use (or default)
        """
        super().__init__()
        self.risk_profile = risk_profile or self._get_default_profile()

    def _get_default_profile(self) -> Optional[RiskProfile]:
        """Get the default risk profile."""
        try:
            return RiskProfile.objects.get(is_default=True)
        except RiskProfile.DoesNotExist:
            return None

    def calculate_position_size(
        self,
        entry_price: Decimal,
        stop_loss: Decimal,
        direction: str = 'buy',
        trading_pair=None,
        signal=None,
        custom_risk_percent: Decimal = None,
    ) -> ServiceResult:
        """
        Calculate position size for a trade.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            direction: 'buy' or 'sell'
            trading_pair: Optional TradingPair model
            signal: Optional Signal model
            custom_risk_percent: Override risk percent

        Returns:
            ServiceResult with position size data
        """
        if not self.risk_profile:
            return self.error_result("No risk profile configured")

        try:
            entry_price = Decimal(str(entry_price))
            stop_loss = Decimal(str(stop_loss))

            # Validate prices
            if direction == 'buy' and stop_loss >= entry_price:
                return self.error_result(
                    "Stop loss must be below entry for buy orders"
                )
            if direction == 'sell' and stop_loss <= entry_price:
                return self.error_result(
                    "Stop loss must be above entry for sell orders"
                )

            # Calculate risk amount
            risk_percent = custom_risk_percent or self.risk_profile.risk_per_trade
            risk_amount = self.risk_profile.account_balance * risk_percent

            # Calculate stop loss distance (in price units)
            if direction == 'buy':
                sl_distance = entry_price - stop_loss
            else:
                sl_distance = stop_loss - entry_price

            # Calculate position size (in base asset units)
            if sl_distance > 0:
                position_size = risk_amount / sl_distance
            else:
                return self.error_result("Invalid stop loss distance")

            # Calculate position value
            position_value = position_size * entry_price

            # Check maximum position size
            max_position_value = (
                self.risk_profile.account_balance *
                self.risk_profile.max_position_size
            )
            if position_value > max_position_value:
                # Reduce position to max allowed
                position_size = max_position_value / entry_price
                position_value = max_position_value
                self.log_warning(
                    f"Position size capped to {self.risk_profile.max_position_size*100}% "
                    f"of balance"
                )

            # Round position size appropriately
            position_size = position_size.quantize(
                Decimal('0.00000001'),
                rounding=ROUND_DOWN
            )

            result_data = {
                'position_size': float(position_size),
                'position_value': float(position_value),
                'risk_amount': float(risk_amount),
                'risk_percent': float(risk_percent),
                'entry_price': float(entry_price),
                'stop_loss': float(stop_loss),
                'sl_distance': float(sl_distance),
                'direction': direction,
                'account_balance': float(self.risk_profile.account_balance),
            }

            # Save calculation if trading_pair provided
            if trading_pair:
                calculation = PositionSizeCalculation.objects.create(
                    risk_profile=self.risk_profile,
                    signal=signal,
                    trading_pair=trading_pair,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    risk_amount=risk_amount,
                    position_size=position_size,
                    position_value=position_value,
                    risk_percent=risk_percent,
                    direction=direction,
                    calculation_details=result_data,
                )
                result_data['calculation_id'] = str(calculation.id)

            return self.success_result(result_data)

        except Exception as e:
            self.log_error(f"Error calculating position size: {str(e)}", exc=e)
            return self.error_result(str(e))

    def calculate_with_take_profit(
        self,
        entry_price: Decimal,
        stop_loss: Decimal,
        take_profit: Decimal,
        direction: str = 'buy',
        trading_pair=None,
        signal=None,
    ) -> ServiceResult:
        """
        Calculate position size with take profit and R:R validation.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            direction: 'buy' or 'sell'
            trading_pair: Optional TradingPair model
            signal: Optional Signal model

        Returns:
            ServiceResult with position size and R:R data
        """
        if not self.risk_profile:
            return self.error_result("No risk profile configured")

        try:
            entry_price = Decimal(str(entry_price))
            stop_loss = Decimal(str(stop_loss))
            take_profit = Decimal(str(take_profit))

            # Calculate risk and reward distances
            if direction == 'buy':
                risk_distance = entry_price - stop_loss
                reward_distance = take_profit - entry_price
            else:
                risk_distance = stop_loss - entry_price
                reward_distance = entry_price - take_profit

            # Calculate risk/reward ratio
            if risk_distance > 0:
                risk_reward_ratio = reward_distance / risk_distance
            else:
                return self.error_result("Invalid risk distance")

            # Check minimum R:R
            if risk_reward_ratio < self.risk_profile.min_risk_reward:
                return self.error_result(
                    f"Risk/reward ratio {float(risk_reward_ratio):.2f} is below "
                    f"minimum {float(self.risk_profile.min_risk_reward):.2f}"
                )

            # Calculate position size
            result = self.calculate_position_size(
                entry_price=entry_price,
                stop_loss=stop_loss,
                direction=direction,
                trading_pair=trading_pair,
                signal=signal,
            )

            if not result.success:
                return result

            # Add R:R data
            result.data['take_profit'] = float(take_profit)
            result.data['risk_reward_ratio'] = float(risk_reward_ratio)
            result.data['reward_distance'] = float(reward_distance)
            result.data['potential_profit'] = (
                result.data['risk_amount'] * float(risk_reward_ratio)
            )

            # Update calculation record
            if 'calculation_id' in result.data:
                PositionSizeCalculation.objects.filter(
                    id=result.data['calculation_id']
                ).update(
                    take_profit=take_profit,
                    risk_reward_ratio=risk_reward_ratio,
                )

            return result

        except Exception as e:
            self.log_error(f"Error calculating with TP: {str(e)}", exc=e)
            return self.error_result(str(e))

    def calculate_for_fixed_size(
        self,
        entry_price: Decimal,
        position_size: Decimal,
        direction: str = 'buy',
        risk_percent: Decimal = None,
    ) -> ServiceResult:
        """
        Calculate stop loss for a fixed position size.

        Reverse calculation: given position size, find the
        appropriate stop loss distance.

        Args:
            entry_price: Entry price
            position_size: Fixed position size
            direction: 'buy' or 'sell'
            risk_percent: Risk percent (default from profile)

        Returns:
            ServiceResult with stop loss data
        """
        if not self.risk_profile:
            return self.error_result("No risk profile configured")

        try:
            entry_price = Decimal(str(entry_price))
            position_size = Decimal(str(position_size))
            risk_percent = risk_percent or self.risk_profile.risk_per_trade

            # Calculate risk amount
            risk_amount = self.risk_profile.account_balance * risk_percent

            # Calculate stop loss distance
            sl_distance = risk_amount / position_size

            # Calculate stop loss price
            if direction == 'buy':
                stop_loss = entry_price - sl_distance
            else:
                stop_loss = entry_price + sl_distance

            return self.success_result({
                'entry_price': float(entry_price),
                'position_size': float(position_size),
                'stop_loss': float(stop_loss),
                'sl_distance': float(sl_distance),
                'risk_amount': float(risk_amount),
                'risk_percent': float(risk_percent),
                'direction': direction,
            })

        except Exception as e:
            self.log_error(f"Error calculating for fixed size: {str(e)}", exc=e)
            return self.error_result(str(e))
