"""
Celery tasks for the risk_management app.
"""

from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger('trading_bot')


@shared_task
def reset_daily_trackers_task():
    """Reset daily trackers at start of new day."""
    from .models import DailyRiskTracker, RiskProfile

    today = timezone.now().date()
    profiles = RiskProfile.objects.filter(is_active=True)

    created_count = 0
    for profile in profiles:
        tracker, created = DailyRiskTracker.objects.get_or_create(
            risk_profile=profile,
            date=today,
        )
        if created:
            created_count += 1

    logger.info(f"Created {created_count} new daily trackers")
    return {'created': created_count}


@shared_task
def cleanup_old_calculations_task(days: int = 90):
    """Delete old position size calculations."""
    from .models import PositionSizeCalculation

    cutoff = timezone.now() - timezone.timedelta(days=days)
    deleted, _ = PositionSizeCalculation.objects.filter(created_at__lt=cutoff).delete()

    logger.info(f"Deleted {deleted} old calculations")
    return {'deleted': deleted}
