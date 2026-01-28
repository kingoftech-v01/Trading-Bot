"""
Position Manager - Manages open positions.
"""

from typing import List, Optional
from decimal import Decimal
import logging

from apps.core.services.base_service import BaseService, ServiceResult
from ..models import Position, Trade


logger = logging.getLogger('trading_bot')


class PositionManager(BaseService):
    """Manages positions and monitors for SL/TP triggers."""

    def get_open_positions(self, trading_pair=None) -> List[Position]:
        """Get all open positions."""
        queryset = Position.objects.filter(is_active=True)
        if trading_pair:
            queryset = queryset.filter(trading_pair=trading_pair)
        return list(queryset.select_related('trading_pair'))

    def update_position_prices(self, trading_pair, current_price: Decimal):
        """Update unrealized P&L for positions."""
        positions = Position.objects.filter(
            trading_pair=trading_pair,
            is_active=True,
        )
        for position in positions:
            position.update_pnl(current_price)

    def check_stop_loss_take_profit(
        self,
        position: Position,
        current_price: Decimal,
    ) -> ServiceResult:
        """Check if SL or TP is hit."""
        triggers = []

        if position.stop_loss:
            if position.side == 'long' and current_price <= position.stop_loss:
                triggers.append(('stop_loss', position.stop_loss))
            elif position.side == 'short' and current_price >= position.stop_loss:
                triggers.append(('stop_loss', position.stop_loss))

        if position.take_profit:
            if position.side == 'long' and current_price >= position.take_profit:
                triggers.append(('take_profit', position.take_profit))
            elif position.side == 'short' and current_price <= position.take_profit:
                triggers.append(('take_profit', position.take_profit))

        return self.success_result({
            'triggers': triggers,
            'position_id': str(position.id),
            'current_price': float(current_price),
        })

    def get_position_summary(self) -> ServiceResult:
        """Get summary of all positions."""
        positions = self.get_open_positions()

        total_unrealized_pnl = sum(
            p.unrealized_pnl or Decimal('0') for p in positions
        )
        long_positions = [p for p in positions if p.side == 'long']
        short_positions = [p for p in positions if p.side == 'short']

        return self.success_result({
            'total_positions': len(positions),
            'long_count': len(long_positions),
            'short_count': len(short_positions),
            'total_unrealized_pnl': float(total_unrealized_pnl),
            'positions': [
                {
                    'id': str(p.id),
                    'pair': p.trading_pair.symbol,
                    'side': p.side,
                    'quantity': float(p.quantity),
                    'entry_price': float(p.average_entry_price),
                    'unrealized_pnl': float(p.unrealized_pnl or 0),
                }
                for p in positions
            ],
        })
