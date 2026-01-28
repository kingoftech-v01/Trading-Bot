"""Alert Manager - Handles system alerts."""

from typing import Dict, Any, Optional
from django.utils import timezone
import logging

from apps.core.services.base_service import BaseService, ServiceResult
from ..models import Alert


logger = logging.getLogger('trading_bot')


class AlertManager(BaseService):
    """Manages alerts and notifications."""

    def create_alert(
        self,
        alert_type: str,
        title: str,
        message: str,
        severity: str = 'info',
        source: str = '',
        metadata: Dict = None,
    ) -> ServiceResult:
        """Create a new alert."""
        try:
            alert = Alert.objects.create(
                alert_type=alert_type,
                severity=severity,
                title=title,
                message=message,
                source=source,
                metadata=metadata or {},
            )

            self.log_info(f"Alert created: {alert}")

            return self.success_result({
                'alert_id': str(alert.id),
                'title': alert.title,
                'severity': alert.severity,
            })

        except Exception as e:
            self.log_error(f"Error creating alert: {str(e)}", exc=e)
            return self.error_result(str(e))

    def acknowledge_alert(self, alert_id: str) -> ServiceResult:
        """Acknowledge an alert."""
        try:
            alert = Alert.objects.get(id=alert_id)
            alert.status = 'acknowledged'
            alert.acknowledged_at = timezone.now()
            alert.save()

            return self.success_result({'status': 'acknowledged'})

        except Alert.DoesNotExist:
            return self.error_result('Alert not found')

    def resolve_alert(self, alert_id: str) -> ServiceResult:
        """Resolve an alert."""
        try:
            alert = Alert.objects.get(id=alert_id)
            alert.status = 'resolved'
            alert.resolved_at = timezone.now()
            alert.save()

            return self.success_result({'status': 'resolved'})

        except Alert.DoesNotExist:
            return self.error_result('Alert not found')

    def get_active_alerts(self, severity: str = None):
        """Get active alerts."""
        queryset = Alert.objects.filter(status='active')
        if severity:
            queryset = queryset.filter(severity=severity)
        return list(queryset.order_by('-created_at'))

    def get_alert_summary(self) -> Dict[str, int]:
        """Get alert counts by severity."""
        from django.db.models import Count

        counts = Alert.objects.filter(status='active').values('severity').annotate(count=Count('id'))
        return {item['severity']: item['count'] for item in counts}
