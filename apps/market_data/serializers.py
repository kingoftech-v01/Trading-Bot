"""
Market Data Serializers - DRF serializers for API endpoints.

Provides serializers for:
- Exchange
- TradingPair
- OHLCV
- CorrelationMatrix
"""

from rest_framework import serializers
from .models import Exchange, TradingPair, OHLCV, CorrelationMatrix


class ExchangeSerializer(serializers.ModelSerializer):
    """Serializer for Exchange model."""

    class Meta:
        model = Exchange
        fields = [
            'id', 'name', 'api_type', 'base_url', 'is_enabled',
            'rate_limit', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExchangeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for Exchange list views."""

    class Meta:
        model = Exchange
        fields = ['id', 'name', 'api_type', 'is_enabled']


class TradingPairSerializer(serializers.ModelSerializer):
    """Serializer for TradingPair model."""
    exchange_name = serializers.CharField(source='exchange.name', read_only=True)
    display_symbol = serializers.CharField(read_only=True)

    class Meta:
        model = TradingPair
        fields = [
            'id', 'symbol', 'display_symbol', 'base_currency', 'quote_currency',
            'exchange', 'exchange_name', 'pip_value', 'min_lot_size', 'max_lot_size',
            'is_forex', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'display_symbol']


class TradingPairListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for TradingPair list views."""
    display_symbol = serializers.CharField(read_only=True)

    class Meta:
        model = TradingPair
        fields = ['id', 'symbol', 'display_symbol', 'is_forex']


class OHLCVSerializer(serializers.ModelSerializer):
    """Serializer for OHLCV model."""
    trading_pair_symbol = serializers.CharField(
        source='trading_pair.symbol',
        read_only=True
    )
    is_bullish = serializers.BooleanField(read_only=True)
    range = serializers.DecimalField(
        max_digits=20,
        decimal_places=8,
        read_only=True
    )

    class Meta:
        model = OHLCV
        fields = [
            'id', 'trading_pair', 'trading_pair_symbol', 'timeframe',
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'is_bullish', 'range', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'is_bullish', 'range']


class OHLCVListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for OHLCV list views (for charts)."""

    class Meta:
        model = OHLCV
        fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']


class OHLCVCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating OHLCV records."""

    class Meta:
        model = OHLCV
        fields = [
            'trading_pair', 'timeframe', 'timestamp',
            'open', 'high', 'low', 'close', 'volume'
        ]


class CorrelationMatrixSerializer(serializers.ModelSerializer):
    """Serializer for CorrelationMatrix model."""
    primary_pair_symbol = serializers.CharField(
        source='primary_pair.symbol',
        read_only=True
    )
    secondary_pair_symbol = serializers.CharField(
        source='secondary_pair.symbol',
        read_only=True
    )
    is_strong_positive = serializers.BooleanField(read_only=True)
    is_strong_negative = serializers.BooleanField(read_only=True)

    class Meta:
        model = CorrelationMatrix
        fields = [
            'id', 'primary_pair', 'primary_pair_symbol',
            'secondary_pair', 'secondary_pair_symbol',
            'timeframe', 'correlation_value', 'calculation_date',
            'lookback_periods', 'is_strong_positive', 'is_strong_negative',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'is_strong_positive', 'is_strong_negative']


class FetchDataSerializer(serializers.Serializer):
    """Serializer for data fetch requests."""
    trading_pair_id = serializers.UUIDField()
    timeframe = serializers.ChoiceField(choices=['15m', '1h', '4h', '1d'])
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    limit = serializers.IntegerField(min_value=1, max_value=1000, default=100)
