"""
Serializers for the signals app.

Following URL_AND_VIEW_CONVENTIONS.md:
- Serializers for REST API responses
- Used by views_api.py ViewSets
"""

from rest_framework import serializers
from .models import Vote, SignalSession, Signal, ConfluenceScore


class VoteSerializer(serializers.ModelSerializer):
    """Serializer for Vote model."""

    combination_name = serializers.CharField(
        source='combination.name',
        read_only=True
    )
    combination_display_name = serializers.CharField(
        source='combination.display_name',
        read_only=True
    )

    class Meta:
        model = Vote
        fields = [
            'id',
            'combination',
            'combination_name',
            'combination_display_name',
            'trading_pair',
            'signal_session',
            'timeframe',
            'signal',
            'confidence',
            'criteria_met',
            'indicator_values',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class VoteListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for vote lists."""

    combination_name = serializers.CharField(
        source='combination.display_name',
        read_only=True
    )

    class Meta:
        model = Vote
        fields = [
            'id',
            'combination_name',
            'signal',
            'confidence',
        ]


class SignalSessionSerializer(serializers.ModelSerializer):
    """Serializer for SignalSession model."""

    trading_pair_symbol = serializers.CharField(
        source='trading_pair.symbol',
        read_only=True
    )
    votes = VoteListSerializer(many=True, read_only=True)
    is_actionable = serializers.BooleanField(read_only=True)
    dominant_direction = serializers.CharField(read_only=True)

    class Meta:
        model = SignalSession
        fields = [
            'id',
            'trading_pair',
            'trading_pair_symbol',
            'timeframe',
            'final_signal',
            'buy_votes',
            'sell_votes',
            'neutral_votes',
            'voting_threshold',
            'confluence_score',
            'average_confidence',
            'evaluated_at',
            'is_actionable',
            'dominant_direction',
            'votes',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'evaluated_at']


class SignalSessionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for session lists."""

    trading_pair_symbol = serializers.CharField(
        source='trading_pair.symbol',
        read_only=True
    )

    class Meta:
        model = SignalSession
        fields = [
            'id',
            'trading_pair_symbol',
            'timeframe',
            'final_signal',
            'buy_votes',
            'sell_votes',
            'confluence_score',
            'evaluated_at',
        ]


class SignalSerializer(serializers.ModelSerializer):
    """Serializer for Signal model."""

    trading_pair_symbol = serializers.CharField(
        source='trading_pair.symbol',
        read_only=True
    )
    session_data = SignalSessionListSerializer(
        source='session',
        read_only=True
    )
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Signal
        fields = [
            'id',
            'session',
            'session_data',
            'trading_pair',
            'trading_pair_symbol',
            'timeframe',
            'signal',
            'status',
            'vote_count',
            'confluence_score',
            'confidence',
            'entry_price',
            'stop_loss',
            'take_profit',
            'risk_reward_ratio',
            'expires_at',
            'executed_at',
            'is_expired',
            'metadata',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class SignalListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for signal lists."""

    trading_pair_symbol = serializers.CharField(
        source='trading_pair.symbol',
        read_only=True
    )

    class Meta:
        model = Signal
        fields = [
            'id',
            'trading_pair_symbol',
            'timeframe',
            'signal',
            'status',
            'vote_count',
            'confluence_score',
            'entry_price',
            'created_at',
        ]


class ConfluenceScoreSerializer(serializers.ModelSerializer):
    """Serializer for ConfluenceScore model."""

    trading_pair_symbol = serializers.CharField(
        source='trading_pair.symbol',
        read_only=True
    )

    class Meta:
        model = ConfluenceScore
        fields = [
            'id',
            'session',
            'trading_pair',
            'trading_pair_symbol',
            'timeframe',
            'total_score',
            'vote_weight_score',
            'confidence_score',
            'win_rate_score',
            'risk_reward_score',
            'indicator_alignment_score',
            'scoring_breakdown',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class GenerateSignalSerializer(serializers.Serializer):
    """Serializer for signal generation request."""

    trading_pair_id = serializers.UUIDField(
        help_text="UUID of the trading pair"
    )
    timeframe = serializers.ChoiceField(
        choices=['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'],
        default='1h',
        help_text="Timeframe for analysis"
    )
    min_confluence = serializers.FloatField(
        required=False,
        default=50.0,
        min_value=0,
        max_value=100,
        help_text="Minimum confluence score required"
    )
    min_confidence = serializers.FloatField(
        required=False,
        default=60.0,
        min_value=0,
        max_value=100,
        help_text="Minimum confidence required"
    )


class SignalGenerationResultSerializer(serializers.Serializer):
    """Serializer for signal generation result."""

    signal_generated = serializers.BooleanField()
    signal = serializers.CharField(allow_null=True)
    signal_id = serializers.UUIDField(allow_null=True)
    session_id = serializers.UUIDField(allow_null=True)
    vote_count = serializers.IntegerField()
    confluence_score = serializers.FloatField()
    average_confidence = serializers.FloatField()
    entry_price = serializers.FloatField(allow_null=True)
    stop_loss = serializers.FloatField(allow_null=True)
    take_profit = serializers.FloatField(allow_null=True)
    risk_reward_ratio = serializers.FloatField(allow_null=True)
    voting_summary = serializers.DictField()
    reason = serializers.CharField(allow_null=True, required=False)


class VotingSummarySerializer(serializers.Serializer):
    """Serializer for voting summary."""

    final_signal = serializers.CharField()
    buy_count = serializers.IntegerField()
    sell_count = serializers.IntegerField()
    neutral_count = serializers.IntegerField()
    threshold = serializers.IntegerField()
    threshold_met = serializers.BooleanField()
    confluence_score = serializers.FloatField()
    average_confidence = serializers.FloatField()
    buy_combinations = serializers.ListField(child=serializers.CharField())
    sell_combinations = serializers.ListField(child=serializers.CharField())
