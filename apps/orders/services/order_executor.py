"""
Order Executor - Handles order execution.
"""

from typing import Dict, Any, Optional
from decimal import Decimal
from django.utils import timezone
import logging

from apps.core.services.base_service import BaseService, ServiceResult
from ..models import Order, Trade, Position


logger = logging.getLogger('trading_bot')


class OrderExecutor(BaseService):
    """Executes orders and manages the order lifecycle."""

    def create_order(
        self,
        trading_pair,
        side: str,
        quantity: Decimal,
        order_type: str = 'market',
        price: Decimal = None,
        stop_loss: Decimal = None,
        take_profit: Decimal = None,
        signal=None,
        timeframe: str = '1h',
    ) -> ServiceResult:
        """Create a new order."""
        try:
            order = Order.objects.create(
                trading_pair=trading_pair,
                signal=signal,
                order_type=order_type,
                side=side,
                price=price,
                quantity=quantity,
                stop_loss=stop_loss,
                take_profit=take_profit,
                timeframe=timeframe,
                status='pending',
            )

            self.log_info(f"Created order: {order}")

            return self.success_result({
                'order_id': str(order.id),
                'order': {
                    'side': order.side,
                    'quantity': float(order.quantity),
                    'price': float(order.price) if order.price else None,
                    'status': order.status,
                },
            })

        except Exception as e:
            self.log_error(f"Error creating order: {str(e)}", exc=e)
            return self.error_result(str(e))

    def execute_order(self, order: Order) -> ServiceResult:
        """Execute an order (simulated for now)."""
        try:
            # For simulation/backtesting - execute at current price
            order.status = 'filled'
            order.filled_quantity = order.quantity
            order.average_fill_price = order.price or order.trading_pair.get_current_price()
            order.filled_at = timezone.now()
            order.save()

            # Create trade
            trade_side = 'long' if order.side == 'buy' else 'short'
            trade = Trade.objects.create(
                trading_pair=order.trading_pair,
                signal=order.signal,
                entry_order=order,
                side=trade_side,
                entry_price=order.average_fill_price,
                quantity=order.filled_quantity,
                stop_loss=order.stop_loss,
                take_profit=order.take_profit,
                timeframe=order.timeframe,
            )

            self.log_info(f"Order executed: {order}, Trade created: {trade}")

            return self.success_result({
                'order_id': str(order.id),
                'trade_id': str(trade.id),
                'fill_price': float(order.average_fill_price),
                'filled_quantity': float(order.filled_quantity),
            })

        except Exception as e:
            self.log_error(f"Error executing order: {str(e)}", exc=e)
            return self.error_result(str(e))

    def cancel_order(self, order: Order) -> ServiceResult:
        """Cancel an order."""
        try:
            if order.status in ['filled', 'cancelled']:
                return self.error_result(f"Cannot cancel order with status: {order.status}")

            order.status = 'cancelled'
            order.cancelled_at = timezone.now()
            order.save()

            return self.success_result({'order_id': str(order.id), 'status': 'cancelled'})

        except Exception as e:
            self.log_error(f"Error cancelling order: {str(e)}", exc=e)
            return self.error_result(str(e))

    def close_trade(
        self,
        trade: Trade,
        exit_price: Decimal,
        close_reason: str = 'manual',
    ) -> ServiceResult:
        """Close a trade."""
        try:
            trade.exit_price = exit_price
            trade.close_reason = close_reason
            trade.status = 'closed'
            trade.closed_at = timezone.now()
            trade.calculate_pnl()
            trade.save()

            self.log_info(
                f"Trade closed: {trade}, P&L: {trade.realized_pnl}"
            )

            return self.success_result({
                'trade_id': str(trade.id),
                'realized_pnl': float(trade.realized_pnl),
                'realized_pnl_percent': float(trade.realized_pnl_percent),
            })

        except Exception as e:
            self.log_error(f"Error closing trade: {str(e)}", exc=e)
            return self.error_result(str(e))
