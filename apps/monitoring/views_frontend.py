"""Frontend Views for the monitoring app."""

from django.views.generic import ListView, DetailView, TemplateView
from django.utils import timezone

from .models import Alert, HealthCheck, Report
from .services import AlertManager, HealthChecker, ReportGenerator


class AlertListView(ListView):
    model = Alert
    template_name = 'monitoring/alert_list.html'
    context_object_name = 'alerts'
    paginate_by = 50


class AlertDetailView(DetailView):
    model = Alert
    template_name = 'monitoring/alert_detail.html'
    context_object_name = 'alert'


class ReportListView(ListView):
    model = Report
    template_name = 'monitoring/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20


class ReportDetailView(DetailView):
    model = Report
    template_name = 'monitoring/report_detail.html'
    context_object_name = 'report'


class MonitoringDashboardView(TemplateView):
    template_name = 'monitoring/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Health
        checker = HealthChecker()
        health_result = checker.check_all()
        context['health'] = health_result.data if health_result.success else None

        # Alerts
        manager = AlertManager()
        context['active_alerts'] = manager.get_active_alerts()[:10]
        context['alert_summary'] = manager.get_alert_summary()

        # Recent reports
        context['recent_reports'] = Report.objects.order_by('-created_at')[:5]

        return context


class SystemDashboardView(TemplateView):
    """Main system dashboard combining all apps."""
    template_name = 'monitoring/system_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from apps.signals.models import Signal, SignalSession
        from apps.orders.models import Trade, Position
        from apps.market_data.models import TradingPair

        # Active signals
        context['active_signals'] = Signal.objects.filter(
            status='pending',
            expires_at__gt=timezone.now(),
        ).count()

        # Recent sessions
        context['recent_sessions'] = SignalSession.objects.order_by('-evaluated_at')[:5]

        # Open positions
        context['open_positions'] = Position.objects.filter(is_active=True).count()

        # Today's trades
        today_start = timezone.now().replace(hour=0, minute=0, second=0)
        context['today_trades'] = Trade.objects.filter(opened_at__gte=today_start).count()

        # Active pairs
        context['active_pairs'] = TradingPair.objects.filter(is_active=True).count()

        # Health
        checker = HealthChecker()
        health_result = checker.check_all()
        context['health'] = health_result.data if health_result.success else None

        # Alerts
        manager = AlertManager()
        context['alert_summary'] = manager.get_alert_summary()

        return context
