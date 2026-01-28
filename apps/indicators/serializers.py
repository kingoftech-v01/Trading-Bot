"""
Indicators Serializers - DRF serializers for API endpoints.
"""

from rest_framework import serializers
from .models import IndicatorType, IndicatorConfig, IndicatorResult


class IndicatorTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndicatorType
        fields = ['id', 'name', 'display_name', 'description', 'default_params', 'output_fields']


class IndicatorConfigSerializer(serializers.ModelSerializer):
    indicator_name = serializers.CharField(source='indicator_type.name', read_only=True)
    trading_pair_symbol = serializers.CharField(source='trading_pair.symbol', read_only=True)

    class Meta:
        model = IndicatorConfig
        fields = [
            'id', 'indicator_type', 'indicator_name', 'trading_pair',
            'trading_pair_symbol', 'timeframe', 'params', 'is_enabled'
        ]


class IndicatorResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndicatorResult
        fields = ['id', 'config', 'timestamp', 'values', 'created_at']


class CalculateIndicatorSerializer(serializers.Serializer):
    """Serializer for indicator calculation requests."""
    trading_pair_id = serializers.UUIDField()
    timeframe = serializers.ChoiceField(choices=['15m', '1h', '4h', '1d'])
    indicators = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text='List of indicator names to calculate'
    )
    limit = serializers.IntegerField(min_value=10, max_value=500, default=100)
