"""Serializers for the orders app."""

from rest_framework import serializers
from .models import Order, Trade, Position


class OrderSerializer(serializers.ModelSerializer):
    trading_pair_symbol = serializers.CharField(source='trading_pair.symbol', read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class TradeSerializer(serializers.ModelSerializer):
    trading_pair_symbol = serializers.CharField(source='trading_pair.symbol', read_only=True)
    is_profitable = serializers.BooleanField(read_only=True)

    class Meta:
        model = Trade
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class PositionSerializer(serializers.ModelSerializer):
    trading_pair_symbol = serializers.CharField(source='trading_pair.symbol', read_only=True)

    class Meta:
        model = Position
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class CreateOrderSerializer(serializers.Serializer):
    trading_pair_id = serializers.UUIDField()
    side = serializers.ChoiceField(choices=['buy', 'sell'])
    quantity = serializers.DecimalField(max_digits=20, decimal_places=8)
    order_type = serializers.ChoiceField(choices=['market', 'limit'], default='market')
    price = serializers.DecimalField(max_digits=20, decimal_places=8, required=False)
    stop_loss = serializers.DecimalField(max_digits=20, decimal_places=8, required=False)
    take_profit = serializers.DecimalField(max_digits=20, decimal_places=8, required=False)
