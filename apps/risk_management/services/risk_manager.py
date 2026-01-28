"""
Risk Manager - Central risk management orchestrator.

Coordinates all risk management functions and enforces
risk limits across the trading system.
"""

from typing import Dict, Any, Optional
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum
import logging

from apps.core.services.base_service import BaseService, ServiceResult
from ..models import RiskProfile, DailyRiskTracker, PositionSizeCalculation
from .position_sizer import PositionSizer
from .stop_loss_calculator import StopLossCalculator
from .take_profit_calculator import TakeProfitCalculator


logger = logging.getLogger('trading_bot')


class RiskManager(BaseService):
    """
    Central risk management service.

    Responsibilities:
    1. Enforce risk limits (per trade, daily, position count)
    2. Calculate position sizes
    3. Determine stop loss and take profit levels
    4. Track daily risk exposure
    5. Validate trades against risk rules
    """

    def __init__(self, risk_profile: RiskProfile = None):
        """
        Initialize risk manager.

        Args:
            risk_profile: RiskProfile to use (or default)
        """
        super().__init__()
        self.risk_profile = risk_profile or self._get_default_profile()
        self.position_sizer = PositionSizer(self.risk_profile)
        self.sl_calculator = StopLossCalculator()
        self.tp_calculator = TakeProfitCalculator()

    def _get_default_profile(self) -> Optional[RiskProfile]:
        """Get the default risk profile."""
        try:
            return RiskProfile.objects.get(is_default=True)
        except RiskProfile.DoesNotExist:
            return None

    def calculate_trade_parameters(
        self,
        entry_price: Decimal,
        direction: str,
        trading_pair=None,
        signal=None,
        atr: Decimal = None,
        support: Decimal = None,
        resistance: Decimal = None,
        custom_sl: Decimal = None,
        custom_tp: Decimal = None,
    ) -> ServiceResult:
        """
        Calculate complete trade parameters.

        Args:
            entry_price: Entry price
            direction: 'buy' or 'sell'
            trading_pair: Optional TradingPair model
            signal: Optional Signal model
            atr: ATR value for volatility-based levels
            support: Support level
            resistance: Resistance level
            custom_sl: Custom stop loss (override)
            custom_tp: Custom take profit (override)

        Returns:
            ServiceResult with complete trade parameters
        """
        if not self.risk_profile:
            return self.error_result("No risk profile configured")

        try:
            entry_price = Decimal(str(entry_price))

            # Step 1: Calculate stop loss
            if custom_sl:
                stop_loss = Decimal(str(custom_sl))
            elif atr:
                sl_result = self.sl_calculator.calculate_atr_based(
                    entry_price, atr, direction
                )
                if not sl_result.success:
                    return sl_result
                stop_loss = Decimal(str(sl_result.data['stop_loss']))
            else:
                sl_result = self.sl_calculator.calculate_percentage_based(
                    entry_price, direction
                )
                if not sl_result.success:
                    return sl_result
                stop_loss = Decimal(str(sl_result.data['stop_loss']))

            # Step 2: Calculate take profit
            if custom_tp:
                take_profit = Decimal(str(custom_tp))
            else:
                tp_result = self.tp_calculator.calculate_risk_reward_based(
                    entry_price, stop_loss, direction,
                    risk_reward=float(self.risk_profile.min_risk_reward)
                )
                if not tp_result.success:
                    return tp_result
                take_profit = Decimal(str(tp_result.data['take_profit']))

            # Step 3: Calculate position size
            pos_result = self.position_sizer.calculate_with_take_profit(
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                direction=direction,
                trading_pair=trading_pair,
                signal=signal,
            )

            if not pos_result.success:
                return pos_result

            # Step 4: Validate against risk limits
            validation = self._validate_trade_risk(pos_result.data)
            if not validation['is_valid']:
                return self.error_result(validation['reason'])

            # Combine all data
            result_data = {
                **pos_result.data,
                'stop_loss': float(stop_loss),
                'take_profit': float(take_profit),
                'validation': validation,
            }

            return self.success_result(result_data)

        except Exception as e:
            self.log_error(f"Error calculating trade params: {str(e)}", exc=e)
            return self.error_result(str(e))

    def _validate_trade_risk(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate trade against risk limits.

        Args:
            trade_data: Trade parameters

        Returns:
            Validation result
        """
        if not self.risk_profile:
            return {'is_valid': False, 'reason': 'No risk profile'}

        # Check R:R ratio
        rr = trade_data.get('risk_reward_ratio', 0)
        if rr < float(self.risk_profile.min_risk_reward):
            return {
                'is_valid': False,
                'reason': f"R:R ratio {rr:.2f} below minimum "
                          f"{self.risk_profile.min_risk_reward}"
            }

        # Check daily risk limit
        daily_tracker = self._get_daily_tracker()
        if daily_tracker and daily_tracker.is_limit_reached:
            return {
                'is_valid': False,
                'reason': 'Daily risk limit reached'
            }

        # Check remaining daily risk
        if daily_tracker:
            risk_amount = Decimal(str(trade_data.get('risk_amount', 0)))
            if risk_amount > daily_tracker.remaining_risk:
                return {
                    'is_valid': False,
                    'reason': f"Risk amount {risk_amount} exceeds remaining "
                              f"daily risk {daily_tracker.remaining_risk}"
                }

        return {'is_valid': True, 'reason': 'Trade validated'}

    def _get_daily_tracker(self) -> Optional[DailyRiskTracker]:
        """Get or create today's risk tracker."""
        if not self.risk_profile:
            return None

        today = timezone.now().date()
        tracker, created = DailyRiskTracker.objects.get_or_create(
            risk_profile=self.risk_profile,
            date=today,
        )
        return tracker

    def record_trade_risk(
        self,
        risk_amount: Decimal,
    ) -> ServiceResult:
        """
        Record risk taken for a new trade.

        Args:
            risk_amount: Risk amount for the trade

        Returns:
            ServiceResult with updated tracker
        """
        if not self.risk_profile:
            return self.error_result("No risk profile configured")

        try:
            tracker = self._get_daily_tracker()
            if not tracker:
                return self.error_result("Could not get daily tracker")

            risk_amount = Decimal(str(risk_amount))
            tracker.total_risk_taken += risk_amount
            tracker.total_trades += 1

            # Check if limit reached
            if tracker.total_risk_taken >= self.risk_profile.max_daily_risk_amount:
                tracker.is_limit_reached = True

            tracker.save()

            return self.success_result({
                'total_risk_taken': float(tracker.total_risk_taken),
                'remaining_risk': float(tracker.remaining_risk),
                'risk_utilization': float(tracker.risk_utilization),
                'total_trades': tracker.total_trades,
                'is_limit_reached': tracker.is_limit_reached,
            })

        except Exception as e:
            self.log_error(f"Error recording trade risk: {str(e)}", exc=e)
            return self.error_result(str(e))

    def record_trade_result(
        self,
        pnl: Decimal,
    ) -> ServiceResult:
        """
        Record P&L for a completed trade.

        Args:
            pnl: Profit/loss amount

        Returns:
            ServiceResult with updated tracker
        """
        if not self.risk_profile:
            return self.error_result("No risk profile configured")

        try:
            tracker = self._get_daily_tracker()
            if not tracker:
                return self.error_result("Could not get daily tracker")

            pnl = Decimal(str(pnl))
            tracker.realized_pnl += pnl

            # Update max drawdown
            if pnl < 0 and abs(pnl) > tracker.max_drawdown:
                tracker.max_drawdown = abs(pnl)

            tracker.save()

            return self.success_result({
                'realized_pnl': float(tracker.realized_pnl),
                'max_drawdown': float(tracker.max_drawdown),
            })

        except Exception as e:
            self.log_error(f"Error recording trade result: {str(e)}", exc=e)
            return self.error_result(str(e))

    def can_open_new_trade(self) -> ServiceResult:
        """
        Check if a new trade can be opened.

        Returns:
            ServiceResult with can_trade and reason
        """
        if not self.risk_profile:
            return self.error_result("No risk profile configured")

        try:
            tracker = self._get_daily_tracker()

            # Check daily limit
            if tracker and tracker.is_limit_reached:
                return self.success_result({
                    'can_trade': False,
                    'reason': 'Daily risk limit reached',
                })

            # Check max open positions
            # (Would need to integrate with orders app)
            # For now, just check daily limit

            return self.success_result({
                'can_trade': True,
                'remaining_risk': float(tracker.remaining_risk) if tracker else 0,
                'risk_utilization': float(tracker.risk_utilization) if tracker else 0,
            })

        except Exception as e:
            self.log_error(f"Error checking trade eligibility: {str(e)}", exc=e)
            return self.error_result(str(e))

    def get_risk_summary(self) -> ServiceResult:
        """
        Get current risk summary.

        Returns:
            ServiceResult with risk metrics
        """
        if not self.risk_profile:
            return self.error_result("No risk profile configured")

        try:
            tracker = self._get_daily_tracker()

            # Get recent calculations
            recent_calcs = PositionSizeCalculation.objects.filter(
                risk_profile=self.risk_profile
            ).order_by('-created_at')[:10]

            return self.success_result({
                'profile': {
                    'name': self.risk_profile.name,
                    'account_balance': float(self.risk_profile.account_balance),
                    'risk_per_trade': float(self.risk_profile.risk_per_trade * 100),
                    'max_daily_risk': float(self.risk_profile.max_daily_risk * 100),
                    'min_risk_reward': float(self.risk_profile.min_risk_reward),
                },
                'daily': {
                    'total_risk_taken': float(tracker.total_risk_taken) if tracker else 0,
                    'remaining_risk': float(tracker.remaining_risk) if tracker else 0,
                    'risk_utilization': float(tracker.risk_utilization) if tracker else 0,
                    'total_trades': tracker.total_trades if tracker else 0,
                    'realized_pnl': float(tracker.realized_pnl) if tracker else 0,
                    'is_limit_reached': tracker.is_limit_reached if tracker else False,
                },
                'recent_calculations': [
                    {
                        'pair': calc.trading_pair.symbol,
                        'size': float(calc.position_size),
                        'risk': float(calc.risk_amount),
                        'direction': calc.direction,
                        'created_at': calc.created_at.isoformat(),
                    }
                    for calc in recent_calcs
                ],
            })

        except Exception as e:
            self.log_error(f"Error getting risk summary: {str(e)}", exc=e)
            return self.error_result(str(e))
