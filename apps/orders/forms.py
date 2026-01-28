"""Forms for the orders app."""

from django import forms


class CreateOrderForm(forms.Form):
    trading_pair = forms.UUIDField(widget=forms.Select(attrs={'class': 'form-select'}))
    side = forms.ChoiceField(choices=[('buy', 'Buy'), ('sell', 'Sell')], widget=forms.Select(attrs={'class': 'form-select'}))
    quantity = forms.DecimalField(max_digits=20, decimal_places=8, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    order_type = forms.ChoiceField(choices=[('market', 'Market'), ('limit', 'Limit')], widget=forms.Select(attrs={'class': 'form-select'}))
    price = forms.DecimalField(max_digits=20, decimal_places=8, required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    stop_loss = forms.DecimalField(max_digits=20, decimal_places=8, required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    take_profit = forms.DecimalField(max_digits=20, decimal_places=8, required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
