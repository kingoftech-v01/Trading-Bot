"""
Forms for the risk_management app.
"""

from django import forms
from .models import RiskProfile


class RiskProfileForm(forms.ModelForm):
    """Form for creating/editing RiskProfile."""

    class Meta:
        model = RiskProfile
        fields = [
            'name', 'description', 'account_balance', 'base_currency',
            'risk_per_trade', 'max_daily_risk', 'max_open_positions',
            'max_position_size', 'min_risk_reward', 'use_trailing_stop',
            'trailing_stop_distance', 'is_default', 'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'account_balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'risk_per_trade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'max_daily_risk': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_risk_reward': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }


class CalculatePositionSizeForm(forms.Form):
    """Form for position size calculation."""

    entry_price = forms.DecimalField(
        max_digits=20, decimal_places=8,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    stop_loss = forms.DecimalField(
        max_digits=20, decimal_places=8,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    take_profit = forms.DecimalField(
        max_digits=20, decimal_places=8, required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    direction = forms.ChoiceField(
        choices=[('buy', 'Buy'), ('sell', 'Sell')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
