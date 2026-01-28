"""
Core Forms - Base form classes for the trading bot.

This module provides base form classes that other apps can extend.
"""

from django import forms


class BaseModelForm(forms.ModelForm):
    """
    Base form for all model forms.

    Provides common styling and validation.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add common CSS classes to all form fields
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
