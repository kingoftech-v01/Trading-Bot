"""
Trade Logger - Logs and tracks trade history.
"""

from typing import Dict, Any, List
from decimal import Decimal
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
import logging

from apps.core.services.base_service import BaseService, ServiceResult
from ..models import Trade


logger = logging.getLogger('trading_bot')


class TradeLogger(BaseService):
    """Logs trades and provides performance statistics."""

    def get_trade_statistics(
        self,
        trading_pair=None,
        days: int = 30,
    ) -> ServiceResult:
        """Get trade statistics."""
        try:
            cutoff = timezone.now() - timezone.timedelta(days=days)
            queryset = Trade.objects.filter(
                status='closed',
                closed_at__gte=cutoff,
            )

            if trading_pair:
                queryset = queryset.filter(trading_pair=trading_pair)

            total_trades = queryset.count()
            winning_trades = queryset.filter(realized_pnl__gt=0).count()
            losing_trades = queryset.filter(realized_pnl__lt=0).count()

            total_pnl = queryset.aggregate(Sum('realized_pnl'))['realized_pnl__sum'] or Decimal('0')
            avg_pnl = queryset.aggregate(Avg('realized_pnl'))['realized_pnl__avg'] or Decimal('0')

            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

            # Average win and loss
            avg_win = queryset.filter(realized_pnl__gt=0).aggregate(
                Avg('realized_pnl')
            )['realized_pnl__avg'] or Decimal('0')

            avg_loss = queryset.filter(realized_pnl__lt=0).aggregate(
                Avg('realized_pnl')
            )['realized_pnl__avg'] or Decimal('0')

            # Profit factor
            gross_profit = queryset.filter(realized_pnl__gt=0).aggregate(
                Sum('realized_pnl')
            )['realized_pnl__sum'] or Decimal('0')

            gross_loss = abs(queryset.filter(realized_pnl__lt=0).aggregate(
                Sum('realized_pnl')
            )['realized_pnl__sum'] or Decimal('1'))

            profit_factor = float(gross_profit / gross_loss) if gross_loss > 0 else 0

            return self.success_result({
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': round(win_rate, 2),
                'total_pnl': float(total_pnl),
                'average_pnl': float(avg_pnl),
                'average_win': float(avg_win),
                'average_loss': float(avg_loss),
                'profit_factor': round(profit_factor, 2),
                'period_days': days,
            })

        except Exception as e:
            self.log_error(f"Error getting trade statistics: {str(e)}", exc=e)
            return self.error_result(str(e))

    def get_recent_trades(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent trades."""
        trades = Trade.objects.select_related('trading_pair').order_by('-opened_at')[:limit]

        return [
            {
                'id': str(t.id),
                'pair': t.trading_pair.symbol,
                'side': t.side,
                'entry_price': float(t.entry_price),
                'exit_price': float(t.exit_price) if t.exit_price else None,
                'quantity': float(t.quantity),
                'realized_pnl': float(t.realized_pnl) if t.realized_pnl else None,
                'status': t.status,
                'opened_at': t.opened_at.isoformat(),
                'closed_at': t.closed_at.isoformat() if t.closed_at else None,
            }
            for t in trades
        ]
