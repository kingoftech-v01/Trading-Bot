"""
Forms for the combinations app.

Following URL_AND_VIEW_CONVENTIONS.md:
- Forms for frontend views (HTML templates)
- Used by views_frontend.py
"""

from django import forms
from .models import Combination, CombinationResult


class CombinationForm(forms.ModelForm):
    """Form for creating/editing Combination."""

    class Meta:
        model = Combination
        fields = [
            'name',
            'display_name',
            'description',
            'win_rate',
            'risk_reward_ratio',
            'expected_frequency',
            'required_indicators',
            'buy_criteria',
            'sell_criteria',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'display_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'win_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'max': '100'
            }),
            'risk_reward_ratio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0'
            }),
            'expected_frequency': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'required_indicators': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': '["rsi", "macd", "adx"]'
            }),
            'buy_criteria': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'sell_criteria': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CombinationFilterForm(forms.Form):
    """Form for filtering combinations list."""

    is_active = forms.NullBooleanField(
        required=False,
        widget=forms.Select(
            attrs={'class': 'form-select'},
            choices=[
                ('', 'All'),
                ('true', 'Active'),
                ('false', 'Inactive'),
            ]
        )
    )
    min_win_rate = forms.FloatField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min win rate %'
        })
    )
    min_risk_reward = forms.FloatField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min R:R ratio'
        })
    )


class EvaluateCombinationForm(forms.Form):
    """Form for evaluating combinations."""

    trading_pair = forms.UUIDField(
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    timeframe = forms.ChoiceField(
        choices=[
            ('1m', '1 Minute'),
            ('5m', '5 Minutes'),
            ('15m', '15 Minutes'),
            ('30m', '30 Minutes'),
            ('1h', '1 Hour'),
            ('4h', '4 Hours'),
            ('1d', '1 Day'),
            ('1w', '1 Week'),
        ],
        initial='1h',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    combination = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Leave empty to evaluate all combinations"
    )

    def __init__(self, *args, **kwargs):
        trading_pairs = kwargs.pop('trading_pairs', [])
        combinations = kwargs.pop('combinations', [])
        super().__init__(*args, **kwargs)

        # Populate trading pair choices
        self.fields['trading_pair'].widget.choices = [
            (str(tp.id), tp.symbol) for tp in trading_pairs
        ]

        # Populate combination choices
        combo_choices = [('', 'All Combinations')]
        combo_choices.extend([
            (c.name, c.display_name) for c in combinations
        ])
        self.fields['combination'].choices = combo_choices


class CombinationResultFilterForm(forms.Form):
    """Form for filtering combination results."""

    combination = forms.UUIDField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    trading_pair = forms.UUIDField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    signal = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Signals'),
            ('buy', 'Buy'),
            ('sell', 'Sell'),
            ('neutral', 'Neutral'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    timeframe = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Timeframes'),
            ('1m', '1 Minute'),
            ('5m', '5 Minutes'),
            ('15m', '15 Minutes'),
            ('30m', '30 Minutes'),
            ('1h', '1 Hour'),
            ('4h', '4 Hours'),
            ('1d', '1 Day'),
            ('1w', '1 Week'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    date_to = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
