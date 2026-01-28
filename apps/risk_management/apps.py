"""
App configuration for the risk_management app.
"""

from django.apps import AppConfig


class RiskManagementConfig(AppConfig):
    """Configuration for risk_management app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.risk_management'
    verbose_name = 'Risk Management'

    def ready(self):
        """Import signal handlers when app is ready."""
        pass
