"""
Serializers for the risk_management app.
"""

from rest_framework import serializers
from .models import RiskProfile, PositionSizeCalculation, DailyRiskTracker


class RiskProfileSerializer(serializers.ModelSerializer):
    """Serializer for RiskProfile model."""

    max_risk_amount = serializers.DecimalField(
        max_digits=20, decimal_places=2, read_only=True
    )
    max_daily_risk_amount = serializers.DecimalField(
        max_digits=20, decimal_places=2, read_only=True
    )

    class Meta:
        model = RiskProfile
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class PositionSizeCalculationSerializer(serializers.ModelSerializer):
    """Serializer for PositionSizeCalculation model."""

    trading_pair_symbol = serializers.CharField(
        source='trading_pair.symbol', read_only=True
    )

    class Meta:
        model = PositionSizeCalculation
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class DailyRiskTrackerSerializer(serializers.ModelSerializer):
    """Serializer for DailyRiskTracker model."""

    remaining_risk = serializers.DecimalField(
        max_digits=20, decimal_places=2, read_only=True
    )
    risk_utilization = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )

    class Meta:
        model = DailyRiskTracker
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class CalculatePositionSizeSerializer(serializers.Serializer):
    """Serializer for position size calculation request."""

    entry_price = serializers.DecimalField(max_digits=20, decimal_places=8)
    stop_loss = serializers.DecimalField(max_digits=20, decimal_places=8)
    take_profit = serializers.DecimalField(
        max_digits=20, decimal_places=8, required=False
    )
    direction = serializers.ChoiceField(choices=['buy', 'sell'])
    trading_pair_id = serializers.UUIDField(required=False)
    risk_profile_id = serializers.UUIDField(required=False)
