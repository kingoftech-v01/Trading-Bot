"""
App configuration for the signals app.
"""

from django.apps import AppConfig


class SignalsConfig(AppConfig):
    """Configuration for signals app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.signals'
    verbose_name = 'Signals'

    def ready(self):
        """Import signal handlers when app is ready."""
        pass
