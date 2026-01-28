"""
Serializers for the combinations app.

Following URL_AND_VIEW_CONVENTIONS.md:
- Serializers for REST API responses
- Used by views_api.py ViewSets
"""

from rest_framework import serializers
from .models import Combination, CombinationResult


class CombinationSerializer(serializers.ModelSerializer):
    """Serializer for Combination model."""

    class Meta:
        model = Combination
        fields = [
            'id',
            'name',
            'display_name',
            'description',
            'win_rate',
            'risk_reward_ratio',
            'expected_frequency',
            'required_indicators',
            'buy_criteria',
            'sell_criteria',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CombinationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""

    class Meta:
        model = Combination
        fields = [
            'id',
            'name',
            'display_name',
            'win_rate',
            'risk_reward_ratio',
            'is_active',
        ]


class CombinationResultSerializer(serializers.ModelSerializer):
    """Serializer for CombinationResult model."""

    combination_name = serializers.CharField(
        source='combination.name',
        read_only=True
    )
    combination_display_name = serializers.CharField(
        source='combination.display_name',
        read_only=True
    )
    trading_pair_symbol = serializers.CharField(
        source='trading_pair.symbol',
        read_only=True
    )

    class Meta:
        model = CombinationResult
        fields = [
            'id',
            'combination',
            'combination_name',
            'combination_display_name',
            'trading_pair',
            'trading_pair_symbol',
            'timeframe',
            'signal',
            'confidence',
            'criteria_met',
            'criteria_details',
            'indicator_values',
            'evaluated_at',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class CombinationResultListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for result list views."""

    combination_name = serializers.CharField(
        source='combination.name',
        read_only=True
    )

    class Meta:
        model = CombinationResult
        fields = [
            'id',
            'combination_name',
            'signal',
            'confidence',
            'evaluated_at',
        ]


class EvaluateCombinationSerializer(serializers.Serializer):
    """Serializer for evaluating a single combination."""

    combination_name = serializers.CharField(
        help_text="Name of the combination to evaluate"
    )
    trading_pair_id = serializers.UUIDField(
        help_text="UUID of the trading pair"
    )
    timeframe = serializers.ChoiceField(
        choices=['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'],
        default='1h',
        help_text="Timeframe for analysis"
    )


class EvaluateAllCombinationsSerializer(serializers.Serializer):
    """Serializer for evaluating all combinations."""

    trading_pair_id = serializers.UUIDField(
        help_text="UUID of the trading pair"
    )
    timeframe = serializers.ChoiceField(
        choices=['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'],
        default='1h',
        help_text="Timeframe for analysis"
    )


class CombinationEvaluationResultSerializer(serializers.Serializer):
    """Serializer for evaluation results."""

    combination = serializers.CharField()
    display_name = serializers.CharField()
    signal = serializers.CharField()
    confidence = serializers.IntegerField()
    win_rate = serializers.FloatField()
    risk_reward = serializers.FloatField()
    criteria_met = serializers.DictField()


class AllCombinationsEvaluationResultSerializer(serializers.Serializer):
    """Serializer for all combinations evaluation results."""

    buy_votes = CombinationEvaluationResultSerializer(many=True)
    sell_votes = CombinationEvaluationResultSerializer(many=True)
    neutral_votes = CombinationEvaluationResultSerializer(many=True)
    summary = serializers.DictField()
    details = serializers.DictField()
