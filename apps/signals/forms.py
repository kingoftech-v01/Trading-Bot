"""
Forms for the signals app.

Following URL_AND_VIEW_CONVENTIONS.md:
- Forms for frontend views (HTML templates)
- Used by views_frontend.py
"""

from django import forms
from .models import Signal, SignalSession


class GenerateSignalForm(forms.Form):
    """Form for generating signals."""

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
    min_confluence = forms.FloatField(
        initial=50.0,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '5',
        }),
        help_text="Minimum confluence score required (0-100)"
    )
    min_confidence = forms.FloatField(
        initial=60.0,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '5',
        }),
        help_text="Minimum average confidence required (0-100)"
    )

    def __init__(self, *args, **kwargs):
        trading_pairs = kwargs.pop('trading_pairs', [])
        super().__init__(*args, **kwargs)

        # Populate trading pair choices
        self.fields['trading_pair'].widget.choices = [
            (str(tp.id), tp.symbol) for tp in trading_pairs
        ]


class SignalFilterForm(forms.Form):
    """Form for filtering signals."""

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
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Status'),
            ('pending', 'Pending'),
            ('executed', 'Executed'),
            ('expired', 'Expired'),
            ('cancelled', 'Cancelled'),
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
    min_confluence = forms.FloatField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min confluence'
        })
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


class SignalSessionFilterForm(forms.Form):
    """Form for filtering signal sessions."""

    trading_pair = forms.UUIDField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    final_signal = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All'),
            ('buy', 'Buy'),
            ('sell', 'Sell'),
            ('wait', 'Wait'),
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
    actionable_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Show only sessions with buy/sell signals"
    )


class SignalActionForm(forms.Form):
    """Form for signal actions (execute, cancel)."""

    action = forms.ChoiceField(
        choices=[
            ('execute', 'Mark as Executed'),
            ('cancel', 'Cancel Signal'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Optional notes'
        })
    )
