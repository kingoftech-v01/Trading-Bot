"""
Indicators Forms - Django forms for frontend views.
"""

from django import forms
from apps.core.forms import BaseModelForm
from .models import IndicatorConfig


class IndicatorConfigForm(BaseModelForm):
    class Meta:
        model = IndicatorConfig
        fields = ['indicator_type', 'trading_pair', 'timeframe', 'params', 'is_enabled']
