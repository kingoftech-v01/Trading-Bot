"""Serializers for the backtesting app."""

from rest_framework import serializers
from .models import BacktestRun, BacktestTrade, BacktestResult


class BacktestRunSerializer(serializers.ModelSerializer):
    trading_pair_symbol = serializers.CharField(source='trading_pair.symbol', read_only=True)

    class Meta:
        model = BacktestRun
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'started_at', 'completed_at']


class BacktestTradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BacktestTrade
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class BacktestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = BacktestResult
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class CreateBacktestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    trading_pair_id = serializers.UUIDField()
    timeframe = serializers.CharField(default='1h')
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    initial_balance = serializers.DecimalField(max_digits=20, decimal_places=2, default=10000)
    risk_per_trade = serializers.DecimalField(max_digits=5, decimal_places=4, default=0.01)
    voting_threshold = serializers.IntegerField(default=5)
