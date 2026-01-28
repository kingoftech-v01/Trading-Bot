"""
Celery configuration for Trading Bot.

This module sets up Celery for asynchronous task processing.
Used for:
- Data fetching from APIs
- Indicator calculations
- Signal generation
- Backtesting runs
- Position monitoring
"""

import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_bot.settings.development')

app = Celery('trading_bot')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'fetch-market-data-every-5-minutes': {
        'task': 'apps.market_data.tasks.fetch_all_pairs_data',
        'schedule': 300.0,  # 5 minutes
    },
    'calculate-indicators-every-5-minutes': {
        'task': 'apps.indicators.tasks.calculate_all_indicators',
        'schedule': 300.0,  # 5 minutes
    },
    'generate-signals-every-5-minutes': {
        'task': 'apps.signals.tasks.generate_signals',
        'schedule': 300.0,  # 5 minutes
    },
    'monitor-positions-every-minute': {
        'task': 'apps.orders.tasks.monitor_open_positions',
        'schedule': 60.0,  # 1 minute
    },
    'health-check-every-minute': {
        'task': 'apps.monitoring.tasks.run_health_checks',
        'schedule': 60.0,  # 1 minute
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f'Request: {self.request!r}')
