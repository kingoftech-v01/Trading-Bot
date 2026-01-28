"""Health Checker - System health monitoring."""

from typing import Dict, Any
import time
import logging

from django.db import connection
from django.core.cache import cache

from apps.core.services.base_service import BaseService, ServiceResult
from ..models import HealthCheck


logger = logging.getLogger('trading_bot')


class HealthChecker(BaseService):
    """Monitors system health."""

    def check_all(self) -> ServiceResult:
        """Run all health checks."""
        results = {
            'database': self.check_database(),
            'redis': self.check_redis(),
        }

        overall_status = 'healthy'
        for check in results.values():
            if check['status'] == 'unhealthy':
                overall_status = 'unhealthy'
                break
            elif check['status'] == 'degraded':
                overall_status = 'degraded'

        return self.success_result({
            'overall_status': overall_status,
            'checks': results,
            'timestamp': time.time(),
        })

    def check_database(self) -> Dict[str, Any]:
        """Check database connectivity."""
        start = time.time()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")

            response_time = int((time.time() - start) * 1000)
            status = 'healthy' if response_time < 100 else 'degraded'

            HealthCheck.objects.create(
                component='database',
                status=status,
                response_time_ms=response_time,
            )

            return {
                'status': status,
                'response_time_ms': response_time,
            }

        except Exception as e:
            HealthCheck.objects.create(
                component='database',
                status='unhealthy',
                details={'error': str(e)},
            )
            return {'status': 'unhealthy', 'error': str(e)}

    def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity."""
        start = time.time()
        try:
            cache.set('health_check', 'ok', 10)
            result = cache.get('health_check')

            if result != 'ok':
                raise Exception("Cache read/write failed")

            response_time = int((time.time() - start) * 1000)
            status = 'healthy' if response_time < 50 else 'degraded'

            HealthCheck.objects.create(
                component='redis',
                status=status,
                response_time_ms=response_time,
            )

            return {
                'status': status,
                'response_time_ms': response_time,
            }

        except Exception as e:
            HealthCheck.objects.create(
                component='redis',
                status='unhealthy',
                details={'error': str(e)},
            )
            return {'status': 'unhealthy', 'error': str(e)}

    def get_health_history(self, component: str, hours: int = 24):
        """Get health check history."""
        from django.utils import timezone
        from datetime import timedelta

        cutoff = timezone.now() - timedelta(hours=hours)
        return list(HealthCheck.objects.filter(
            component=component,
            checked_at__gte=cutoff,
        ).order_by('-checked_at').values())
