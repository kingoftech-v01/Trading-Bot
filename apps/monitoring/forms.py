"""Forms for the monitoring app."""

from django import forms


class AlertFilterForm(forms.Form):
    severity = forms.ChoiceField(
        required=False,
        choices=[('', 'All')] + [('info', 'Info'), ('warning', 'Warning'), ('error', 'Error'), ('critical', 'Critical')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All')] + [('active', 'Active'), ('acknowledged', 'Acknowledged'), ('resolved', 'Resolved')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class GenerateReportForm(forms.Form):
    report_type = forms.ChoiceField(
        choices=[('daily', 'Daily'), ('performance', 'Performance')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    days = forms.IntegerField(
        required=False,
        initial=30,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
