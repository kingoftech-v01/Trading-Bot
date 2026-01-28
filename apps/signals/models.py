"""
Models for the signals app.

Implements the voting system and signal generation models.
"""

from django.db import models
from apps.core.models import BaseModel, TimeframeMixin, SignalDirectionMixin


class Vote(BaseModel, TimeframeMixin, SignalDirectionMixin):
    """
    Individual vote from a combination.

    Each Vote represents the opinion of one combination
    for a specific trading pair and timeframe.
    """

    combination = models.ForeignKey(
        'combinations.Combination',
        on_delete=models.CASCADE,
        related_name='votes',
        help_text="The combination that cast this vote"
    )
    trading_pair = models.ForeignKey(
        'market_data.TradingPair',
        on_delete=models.CASCADE,
        related_name='votes',
        help_text="The trading pair being evaluated"
    )
    signal_session = models.ForeignKey(
        'SignalSession',
        on_delete=models.CASCADE,
        related_name='votes',
        help_text="The signal session this vote belongs to"
    )
    confidence = models.IntegerField(
        default=0,
        help_text="Confidence level 0-100"
    )
    criteria_met = models.JSONField(
        default=dict,
        help_text="Dictionary of criteria and their status"
    )
    indicator_values = models.JSONField(
        default=dict,
        help_text="Indicator values used for evaluation"
    )

    class Meta:
        verbose_name = 'Vote'
        verbose_name_plural = 'Votes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['signal_session', 'signal']),
            models.Index(fields=['combination', 'trading_pair']),
        ]

    def __str__(self):
        return f"{self.combination.display_name} - {self.signal} ({self.confidence}%)"


class SignalSession(BaseModel, TimeframeMixin):
    """
    A signal evaluation session.

    Groups all votes from a single evaluation round and
    determines the final signal based on the voting threshold.
    """

    SIGNAL_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
        ('wait', 'Wait'),
    ]

    trading_pair = models.ForeignKey(
        'market_data.TradingPair',
        on_delete=models.CASCADE,
        related_name='signal_sessions',
        help_text="The trading pair being evaluated"
    )
    final_signal = models.CharField(
        max_length=10,
        choices=SIGNAL_CHOICES,
        default='wait',
        help_text="The final signal after voting"
    )
    buy_votes = models.IntegerField(
        default=0,
        help_text="Number of buy votes"
    )
    sell_votes = models.IntegerField(
        default=0,
        help_text="Number of sell votes"
    )
    neutral_votes = models.IntegerField(
        default=0,
        help_text="Number of neutral votes"
    )
    voting_threshold = models.IntegerField(
        default=5,
        help_text="Minimum votes required for signal"
    )
    confluence_score = models.FloatField(
        default=0.0,
        help_text="Confluence score 0-100"
    )
    average_confidence = models.FloatField(
        default=0.0,
        help_text="Average confidence of winning votes"
    )
    evaluated_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the evaluation was performed"
    )

    class Meta:
        verbose_name = 'Signal Session'
        verbose_name_plural = 'Signal Sessions'
        ordering = ['-evaluated_at']
        indexes = [
            models.Index(fields=['trading_pair', 'timeframe']),
            models.Index(fields=['final_signal', 'evaluated_at']),
            models.Index(fields=['evaluated_at']),
        ]

    def __str__(self):
        return f"{self.trading_pair.symbol} - {self.final_signal} ({self.buy_votes}B/{self.sell_votes}S)"

    @property
    def total_votes(self):
        """Total number of votes cast."""
        return self.buy_votes + self.sell_votes + self.neutral_votes

    @property
    def is_actionable(self):
        """Whether this session resulted in an actionable signal."""
        return self.final_signal in ['buy', 'sell']

    @property
    def dominant_direction(self):
        """The dominant voting direction."""
        if self.buy_votes > self.sell_votes:
            return 'buy'
        elif self.sell_votes > self.buy_votes:
            return 'sell'
        return 'neutral'


class Signal(BaseModel, TimeframeMixin, SignalDirectionMixin):
    """
    Generated trading signal.

    Created when a SignalSession meets the voting threshold.
    This is the actionable signal used by the trading system.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('executed', 'Executed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    session = models.OneToOneField(
        SignalSession,
        on_delete=models.CASCADE,
        related_name='generated_signal',
        help_text="The session that generated this signal"
    )
    trading_pair = models.ForeignKey(
        'market_data.TradingPair',
        on_delete=models.CASCADE,
        related_name='signals',
        help_text="The trading pair for this signal"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the signal"
    )
    vote_count = models.IntegerField(
        default=0,
        help_text="Number of votes supporting this signal"
    )
    confluence_score = models.FloatField(
        default=0.0,
        help_text="Overall confluence score 0-100"
    )
    confidence = models.IntegerField(
        default=0,
        help_text="Average confidence of supporting votes"
    )
    entry_price = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Suggested entry price"
    )
    stop_loss = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Suggested stop loss price"
    )
    take_profit = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Suggested take profit price"
    )
    risk_reward_ratio = models.FloatField(
        null=True,
        blank=True,
        help_text="Risk/reward ratio for this signal"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this signal expires"
    )
    executed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this signal was executed"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Additional signal metadata"
    )

    class Meta:
        verbose_name = 'Signal'
        verbose_name_plural = 'Signals'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['trading_pair', 'status']),
            models.Index(fields=['signal', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.trading_pair.symbol} - {self.signal} ({self.vote_count}/8)"

    @property
    def is_expired(self):
        """Check if signal has expired."""
        from django.utils import timezone
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def mark_executed(self):
        """Mark signal as executed."""
        from django.utils import timezone
        self.status = 'executed'
        self.executed_at = timezone.now()
        self.save(update_fields=['status', 'executed_at'])

    def mark_expired(self):
        """Mark signal as expired."""
        self.status = 'expired'
        self.save(update_fields=['status'])

    def mark_cancelled(self):
        """Mark signal as cancelled."""
        self.status = 'cancelled'
        self.save(update_fields=['status'])


class ConfluenceScore(BaseModel, TimeframeMixin):
    """
    Detailed confluence scoring breakdown.

    Stores detailed scoring information for analysis and optimization.
    """

    session = models.OneToOneField(
        SignalSession,
        on_delete=models.CASCADE,
        related_name='confluence_detail',
        help_text="The session this score belongs to"
    )
    trading_pair = models.ForeignKey(
        'market_data.TradingPair',
        on_delete=models.CASCADE,
        related_name='confluence_scores',
        help_text="The trading pair"
    )
    total_score = models.FloatField(
        default=0.0,
        help_text="Total confluence score 0-100"
    )
    vote_weight_score = models.FloatField(
        default=0.0,
        help_text="Score based on vote count"
    )
    confidence_score = models.FloatField(
        default=0.0,
        help_text="Score based on average confidence"
    )
    win_rate_score = models.FloatField(
        default=0.0,
        help_text="Score based on combination win rates"
    )
    risk_reward_score = models.FloatField(
        default=0.0,
        help_text="Score based on risk/reward ratios"
    )
    indicator_alignment_score = models.FloatField(
        default=0.0,
        help_text="Score based on indicator alignment"
    )
    scoring_breakdown = models.JSONField(
        default=dict,
        help_text="Detailed breakdown of scoring"
    )

    class Meta:
        verbose_name = 'Confluence Score'
        verbose_name_plural = 'Confluence Scores'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.trading_pair.symbol} - Score: {self.total_score:.1f}"
