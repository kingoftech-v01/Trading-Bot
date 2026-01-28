"""
Core Serializers - Base serializers for the trading bot.

This module provides base serializer classes that other apps can extend.
"""

from rest_framework import serializers


class BaseModelSerializer(serializers.ModelSerializer):
    """
    Base serializer for all models.

    Automatically includes id, created_at, updated_at, and is_active fields.
    """
    id = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        abstract = True
        fields = ['id', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TimeframeSerializerMixin(serializers.Serializer):
    """Mixin for serializers that include timeframe field."""
    timeframe = serializers.ChoiceField(
        choices=[
            ('15m', '15 Minutes'),
            ('1h', '1 Hour'),
            ('4h', '4 Hours'),
            ('1d', '1 Day'),
        ]
    )


class SignalSerializerMixin(serializers.Serializer):
    """Mixin for serializers that include signal direction."""
    signal = serializers.ChoiceField(
        choices=[
            ('buy', 'Buy'),
            ('sell', 'Sell'),
            ('neutral', 'Neutral'),
            ('wait', 'Wait'),
        ]
    )
