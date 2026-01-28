"""Report Generator - Generates trading reports."""

from typing import Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count, Avg
import logging

from apps.core.services.base_service import BaseService, ServiceResult
from ..models import Report


logger = logging.getLogger('trading_bot')


class ReportGenerator(BaseService):
    """Generates trading and performance reports."""

    def generate_daily_report(self, date: datetime = None) -> ServiceResult:
        """Generate daily trading report."""
        from apps.signals.models import Signal, SignalSession
        from apps.orders.models import Trade

        date = date or timezone.now().date()
        start = timezone.make_aware(datetime.combine(date, datetime.min.time()))
        end = start + timedelta(days=1)

        # Signals
        signals = Signal.objects.filter(created_at__gte=start, created_at__lt=end)
        sessions = SignalSession.objects.filter(evaluated_at__gte=start, evaluated_at__lt=end)

        # Trades
        trades = Trade.objects.filter(opened_at__gte=start, opened_at__lt=end)
        closed_trades = Trade.objects.filter(closed_at__gte=start, closed_at__lt=end)

        total_pnl = closed_trades.aggregate(Sum('realized_pnl'))['realized_pnl__sum'] or Decimal('0')
        winning = closed_trades.filter(realized_pnl__gt=0).count()
        losing = closed_trades.filter(realized_pnl__lt=0).count()

        data = {
            'signals': {
                'total': signals.count(),
                'buy': signals.filter(signal='buy').count(),
                'sell': signals.filter(signal='sell').count(),
            },
            'sessions': {
                'total': sessions.count(),
                'actionable': sessions.filter(final_signal__in=['buy', 'sell']).count(),
            },
            'trades': {
                'opened': trades.count(),
                'closed': closed_trades.count(),
                'winning': winning,
                'losing': losing,
                'win_rate': (winning / closed_trades.count() * 100) if closed_trades.count() > 0 else 0,
            },
            'pnl': {
                'total': float(total_pnl),
            },
        }

        report = Report.objects.create(
            report_type='daily',
            title=f'Daily Report - {date}',
            period_start=start,
            period_end=end,
            data=data,
            summary=f"Signals: {data['signals']['total']}, Trades: {data['trades']['closed']}, P&L: ${data['pnl']['total']:.2f}",
        )

        return self.success_result({
            'report_id': str(report.id),
            'data': data,
        })

    def generate_performance_summary(self, days: int = 30) -> ServiceResult:
        """Generate performance summary."""
        from apps.orders.models import Trade

        end = timezone.now()
        start = end - timedelta(days=days)

        trades = Trade.objects.filter(
            status='closed',
            closed_at__gte=start,
        )

        total_trades = trades.count()
        winning = trades.filter(realized_pnl__gt=0).count()
        total_pnl = trades.aggregate(Sum('realized_pnl'))['realized_pnl__sum'] or Decimal('0')
        avg_pnl = trades.aggregate(Avg('realized_pnl'))['realized_pnl__avg'] or Decimal('0')

        return self.success_result({
            'period_days': days,
            'total_trades': total_trades,
            'winning_trades': winning,
            'win_rate': (winning / total_trades * 100) if total_trades > 0 else 0,
            'total_pnl': float(total_pnl),
            'average_pnl': float(avg_pnl),
        })
