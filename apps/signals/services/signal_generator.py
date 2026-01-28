"""
Signal Generator - Orchestrates signal generation process.

Coordinates the voting system, confluence scoring, and signal creation.
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
from django.utils import timezone
from django.conf import settings
import logging

from apps.core.services.base_service import BaseService, ServiceResult
from .voting_system import VotingSystem, VotingResult
from .confluence_scorer import ConfluenceScorer
from ..models import Signal, SignalSession, Vote, ConfluenceScore


logger = logging.getLogger('trading_bot')


class SignalGenerator(BaseService):
    """
    Main signal generation service.

    Orchestrates the complete signal generation process:
    1. Collect votes from all combinations
    2. Determine if threshold is met
    3. Calculate confluence scores
    4. Generate actionable signal with entry/SL/TP
    """

    def __init__(
        self,
        voting_threshold: int = None,
        min_confluence: float = 50.0,
        min_confidence: float = 60.0,
        signal_validity_hours: int = 4,
    ):
        """
        Initialize the signal generator.

        Args:
            voting_threshold: Minimum votes for signal (default: 5)
            min_confluence: Minimum confluence score required
            min_confidence: Minimum confidence required
            signal_validity_hours: How long signals remain valid
        """
        super().__init__()
        self.voting_system = VotingSystem(voting_threshold)
        self.confluence_scorer = ConfluenceScorer()
        self.min_confluence = min_confluence
        self.min_confidence = min_confidence
        self.signal_validity_hours = signal_validity_hours

    def generate_signal(
        self,
        trading_pair,
        ohlcv_data: List[Dict],
        timeframe: str = '1h',
        save_to_db: bool = True,
    ) -> ServiceResult:
        """
        Generate a trading signal for the given pair.

        Args:
            trading_pair: TradingPair model instance
            ohlcv_data: List of OHLCV dictionaries
            timeframe: Timeframe for analysis
            save_to_db: Whether to save results to database

        Returns:
            ServiceResult with signal data or None if no signal
        """
        try:
            # Step 1: Collect votes from all combinations
            voting_result = self.voting_system.collect_votes(ohlcv_data)

            # Step 2: Create signal session
            session = None
            if save_to_db:
                session = self._create_signal_session(
                    trading_pair, timeframe, voting_result
                )

            # Step 3: Save individual votes
            if save_to_db and session:
                self._save_votes(session, voting_result)

            # Step 4: Calculate detailed confluence score
            confluence_detail = self.confluence_scorer.calculate_detailed_score(
                voting_result
            )

            # Step 5: Save confluence score
            if save_to_db and session:
                self._save_confluence_score(
                    session, trading_pair, timeframe, confluence_detail
                )

            # Step 6: Check if signal should be generated
            is_valid, reason = self.voting_system.validate_signal_strength(
                voting_result,
                self.min_confluence,
                self.min_confidence
            )

            if not is_valid:
                self.log_info(
                    f"No signal for {trading_pair.symbol}: {reason}"
                )
                return self.success_result({
                    'signal_generated': False,
                    'reason': reason,
                    'session_id': str(session.id) if session else None,
                    'voting_summary': self.voting_system.get_voting_summary(
                        voting_result
                    ),
                })

            # Step 7: Calculate entry, SL, TP
            current_price = Decimal(str(ohlcv_data[-1]['close']))
            entry_data = self._calculate_entry_levels(
                voting_result.final_signal,
                current_price,
                ohlcv_data,
            )

            # Step 8: Generate signal
            signal = None
            if save_to_db and session:
                signal = self._create_signal(
                    session,
                    trading_pair,
                    timeframe,
                    voting_result,
                    entry_data,
                )

            self.log_info(
                f"Signal generated for {trading_pair.symbol}: "
                f"{voting_result.final_signal.upper()} "
                f"({len(voting_result.buy_votes)}B/{len(voting_result.sell_votes)}S)"
            )

            return self.success_result({
                'signal_generated': True,
                'signal': voting_result.final_signal,
                'signal_id': str(signal.id) if signal else None,
                'session_id': str(session.id) if session else None,
                'vote_count': voting_result.vote_count,
                'confluence_score': voting_result.confluence_score,
                'average_confidence': voting_result.average_confidence,
                'entry_price': float(entry_data['entry_price']),
                'stop_loss': float(entry_data['stop_loss']),
                'take_profit': float(entry_data['take_profit']),
                'risk_reward_ratio': entry_data['risk_reward_ratio'],
                'voting_summary': self.voting_system.get_voting_summary(
                    voting_result
                ),
            })

        except Exception as e:
            self.log_error(f"Error generating signal: {str(e)}", exc=e)
            return self.error_result(str(e))

    def _create_signal_session(
        self,
        trading_pair,
        timeframe: str,
        voting_result: VotingResult
    ) -> SignalSession:
        """Create a signal session record."""
        from apps.combinations.models import Combination

        session = SignalSession.objects.create(
            trading_pair=trading_pair,
            timeframe=timeframe,
            final_signal=voting_result.final_signal,
            buy_votes=len(voting_result.buy_votes),
            sell_votes=len(voting_result.sell_votes),
            neutral_votes=len(voting_result.neutral_votes),
            voting_threshold=self.voting_system.voting_threshold,
            confluence_score=voting_result.confluence_score,
            average_confidence=voting_result.average_confidence,
        )
        return session

    def _save_votes(
        self,
        session: SignalSession,
        voting_result: VotingResult
    ):
        """Save individual votes to database."""
        from apps.combinations.models import Combination

        all_votes = (
            voting_result.buy_votes +
            voting_result.sell_votes +
            voting_result.neutral_votes
        )

        for vote_data in all_votes:
            try:
                combination = Combination.objects.get(
                    name=vote_data.combination_name
                )
                Vote.objects.create(
                    combination=combination,
                    trading_pair=session.trading_pair,
                    signal_session=session,
                    timeframe=session.timeframe,
                    signal=vote_data.signal,
                    confidence=vote_data.confidence,
                    criteria_met=vote_data.criteria_met,
                )
            except Combination.DoesNotExist:
                self.log_warning(
                    f"Combination not found: {vote_data.combination_name}"
                )

    def _save_confluence_score(
        self,
        session: SignalSession,
        trading_pair,
        timeframe: str,
        confluence_detail: Dict[str, Any]
    ):
        """Save detailed confluence score."""
        ConfluenceScore.objects.create(
            session=session,
            trading_pair=trading_pair,
            timeframe=timeframe,
            total_score=confluence_detail['total_score'],
            vote_weight_score=confluence_detail['vote_weight_score'],
            confidence_score=confluence_detail['confidence_score'],
            win_rate_score=confluence_detail['win_rate_score'],
            risk_reward_score=confluence_detail['risk_reward_score'],
            indicator_alignment_score=confluence_detail.get(
                'indicator_alignment_score', 0
            ),
            scoring_breakdown=confluence_detail,
        )

    def _calculate_entry_levels(
        self,
        signal: str,
        current_price: Decimal,
        ohlcv_data: List[Dict],
        risk_reward_target: float = 3.0,
    ) -> Dict[str, Any]:
        """
        Calculate entry price, stop loss, and take profit.

        Uses ATR-based stop loss placement.

        Args:
            signal: 'buy' or 'sell'
            current_price: Current market price
            ohlcv_data: OHLCV data for ATR calculation
            risk_reward_target: Target risk/reward ratio

        Returns:
            Dictionary with entry, SL, TP levels
        """
        # Calculate ATR for volatility-based levels
        atr = self._calculate_atr(ohlcv_data, period=14)
        atr_decimal = Decimal(str(atr))

        # Stop loss distance: 2x ATR
        sl_distance = atr_decimal * 2

        if signal == 'buy':
            entry_price = current_price
            stop_loss = entry_price - sl_distance
            # TP at risk_reward_target times the risk
            take_profit = entry_price + (sl_distance * Decimal(str(risk_reward_target)))
        else:  # sell
            entry_price = current_price
            stop_loss = entry_price + sl_distance
            take_profit = entry_price - (sl_distance * Decimal(str(risk_reward_target)))

        # Calculate actual risk/reward
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        actual_rr = float(reward / risk) if risk > 0 else 0

        return {
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_reward_ratio': round(actual_rr, 2),
            'atr': atr,
        }

    def _calculate_atr(
        self,
        ohlcv_data: List[Dict],
        period: int = 14
    ) -> float:
        """Calculate Average True Range."""
        if len(ohlcv_data) < period + 1:
            # Not enough data, use simple range
            recent = ohlcv_data[-1]
            return float(recent['high']) - float(recent['low'])

        true_ranges = []
        for i in range(1, len(ohlcv_data)):
            high = float(ohlcv_data[i]['high'])
            low = float(ohlcv_data[i]['low'])
            prev_close = float(ohlcv_data[i-1]['close'])

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)

        # Simple moving average of TR
        atr = sum(true_ranges[-period:]) / period
        return atr

    def _create_signal(
        self,
        session: SignalSession,
        trading_pair,
        timeframe: str,
        voting_result: VotingResult,
        entry_data: Dict[str, Any],
    ) -> Signal:
        """Create the final signal record."""
        expires_at = timezone.now() + timezone.timedelta(
            hours=self.signal_validity_hours
        )

        signal = Signal.objects.create(
            session=session,
            trading_pair=trading_pair,
            timeframe=timeframe,
            signal=voting_result.final_signal,
            vote_count=voting_result.vote_count,
            confluence_score=voting_result.confluence_score,
            confidence=int(voting_result.average_confidence),
            entry_price=entry_data['entry_price'],
            stop_loss=entry_data['stop_loss'],
            take_profit=entry_data['take_profit'],
            risk_reward_ratio=entry_data['risk_reward_ratio'],
            expires_at=expires_at,
            metadata={
                'atr': entry_data['atr'],
                'buy_count': len(voting_result.buy_votes),
                'sell_count': len(voting_result.sell_votes),
            },
        )
        return signal

    def get_active_signals(self, trading_pair=None) -> List[Signal]:
        """
        Get all active (pending) signals.

        Args:
            trading_pair: Optional filter by trading pair

        Returns:
            List of active Signal objects
        """
        queryset = Signal.objects.filter(
            status='pending',
            expires_at__gt=timezone.now(),
        )
        if trading_pair:
            queryset = queryset.filter(trading_pair=trading_pair)

        return list(queryset.order_by('-created_at'))

    def expire_old_signals(self) -> int:
        """
        Mark expired signals as expired.

        Returns:
            Number of signals expired
        """
        expired = Signal.objects.filter(
            status='pending',
            expires_at__lt=timezone.now(),
        ).update(status='expired')

        if expired:
            self.log_info(f"Expired {expired} old signals")

        return expired
