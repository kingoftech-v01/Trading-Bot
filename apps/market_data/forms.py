"""
Market Data Forms - Django forms for frontend views.

Provides forms for:
- Exchange management
- TradingPair management
- Data fetch requests
"""

from django import forms
from apps.core.forms import BaseModelForm
from .models import Exchange, TradingPair, OHLCV


class ExchangeForm(BaseModelForm):
    """Form for creating/editing Exchange."""

    class Meta:
        model = Exchange
        fields = ['name', 'api_type', 'base_url', 'is_enabled', 'rate_limit']


class TradingPairForm(BaseModelForm):
    """Form for creating/editing TradingPair."""

    class Meta:
        model = TradingPair
        fields = [
            'symbol', 'base_currency', 'quote_currency', 'exchange',
            'pip_value', 'min_lot_size', 'max_lot_size', 'is_forex'
        ]


class FetchDataForm(forms.Form):
    """Form for requesting data fetch."""
    trading_pair = forms.ModelChoiceField(
        queryset=TradingPair.objects.filter(is_active=True),
        label='Trading Pair'
    )
    timeframe = forms.ChoiceField(
        choices=[
            ('15m', '15 Minutes'),
            ('1h', '1 Hour'),
            ('4h', '4 Hours'),
            ('1d', '1 Day'),
        ],
        label='Timeframe'
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Start Date'
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='End Date'
    )
    limit = forms.IntegerField(
        min_value=1,
        max_value=1000,
        initial=100,
        label='Limit'
    )
