"""Forms for the backtesting app."""

from django import forms
from .models import BacktestRun


class BacktestRunForm(forms.ModelForm):
    class Meta:
        model = BacktestRun
        fields = ['name', 'trading_pair', 'timeframe', 'start_date', 'end_date',
                  'initial_balance', 'risk_per_trade', 'voting_threshold', 'min_confluence']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }
