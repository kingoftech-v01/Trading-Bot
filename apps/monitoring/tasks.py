"""Celery tasks for the monitoring app."""

from celery import shared_task
import logging

logger = logging.getLogger('trading_bot')


@shared_task
def run_health_checks_task():
    """Run all health checks."""
    from .services import HealthChecker

    checker = HealthChecker()
    result = checker.check_all()

    if result.success:
        logger.info(f"Health check: {result.data['overall_status']}")
        return result.data

    return {'error': result.error}


@shared_task
def generate_daily_report_task():
    """Generate daily report."""
    from .services import ReportGenerator

    generator = ReportGenerator()
    result = generator.generate_daily_report()

    if result.success:
        logger.info(f"Daily report generated: {result.data['report_id']}")
        return result.data

    return {'error': result.error}


@shared_task
def cleanup_old_metrics_task(days: int = 30):
    """Delete old metrics."""
    from django.utils import timezone
    from datetime import timedelta
    from .models import SystemMetric, HealthCheck

    cutoff = timezone.now() - timedelta(days=days)

    metrics_deleted, _ = SystemMetric.objects.filter(recorded_at__lt=cutoff).delete()
    health_deleted, _ = HealthCheck.objects.filter(checked_at__lt=cutoff).delete()

    logger.info(f"Cleaned up {metrics_deleted} metrics, {health_deleted} health checks")

    return {
        'metrics_deleted': metrics_deleted,
        'health_checks_deleted': health_deleted,
    }
