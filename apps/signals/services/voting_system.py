"""
Voting System - Core "5 out of 8" voting logic.

This is the heart of the trading bot's signal generation system.
A signal is only generated when at least 5 of the 8 combinations
agree on the same direction (buy or sell).
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from django.conf import settings
import logging

from apps.core.services.base_service import BaseService, ServiceResult
from apps.combinations.services import CombinationEvaluator


logger = logging.getLogger('trading_bot')


@dataclass
class VoteResult:
    """Result of a single combination vote."""
    combination_name: str
    display_name: str
    signal: str  # 'buy', 'sell', 'neutral'
    confidence: int
    win_rate: float
    risk_reward: float
    criteria_met: Dict[str, bool]


@dataclass
class VotingResult:
    """Result of the voting process."""
    final_signal: str  # 'buy', 'sell', 'wait'
    buy_votes: List[VoteResult]
    sell_votes: List[VoteResult]
    neutral_votes: List[VoteResult]
    vote_count: int
    threshold_met: bool
    confluence_score: float
    average_confidence: float


class VotingSystem(BaseService):
    """
    Implements the "5 out of 8" voting system.

    The voting system evaluates all 8 combinations and determines
    whether enough combinations agree to generate a trading signal.

    Configuration:
        - voting_threshold: Minimum votes required (default: 5)
        - combinations: All 8 combination evaluators
    """

    def __init__(
        self,
        voting_threshold: int = None,
        indicator_engine=None
    ):
        """
        Initialize the voting system.

        Args:
            voting_threshold: Minimum votes required for signal (default: 5)
            indicator_engine: Optional shared indicator engine
        """
        super().__init__()
        self.voting_threshold = voting_threshold or getattr(
            settings, 'TRADING_CONFIG', {}
        ).get('voting_threshold', 5)
        self.combination_evaluator = CombinationEvaluator(indicator_engine)

    def collect_votes(self, ohlcv_data: List[Dict]) -> VotingResult:
        """
        Collect votes from all 8 combinations.

        Args:
            ohlcv_data: List of OHLCV dictionaries (oldest first)

        Returns:
            VotingResult with all votes and final determination
        """
        # Evaluate all combinations
        evaluation_results = self.combination_evaluator.evaluate_all(ohlcv_data)

        # Convert to VoteResult objects
        buy_votes = [
            VoteResult(
                combination_name=v['combination'],
                display_name=v['display_name'],
                signal='buy',
                confidence=v['confidence'],
                win_rate=v['win_rate'],
                risk_reward=v['risk_reward'],
                criteria_met=v['criteria_met'],
            )
            for v in evaluation_results['buy_votes']
        ]

        sell_votes = [
            VoteResult(
                combination_name=v['combination'],
                display_name=v['display_name'],
                signal='sell',
                confidence=v['confidence'],
                win_rate=v['win_rate'],
                risk_reward=v['risk_reward'],
                criteria_met=v['criteria_met'],
            )
            for v in evaluation_results['sell_votes']
        ]

        neutral_votes = [
            VoteResult(
                combination_name=v['combination'],
                display_name=v.get('display_name', v['combination']),
                signal='neutral',
                confidence=v.get('confidence', 0),
                win_rate=v.get('win_rate', 0),
                risk_reward=v.get('risk_reward', 0),
                criteria_met=v.get('criteria_met', {}),
            )
            for v in evaluation_results['neutral_votes']
        ]

        # Determine final signal
        final_signal, vote_count, threshold_met = self._determine_signal(
            buy_votes, sell_votes
        )

        # Calculate confluence score
        winning_votes = buy_votes if final_signal == 'buy' else sell_votes
        confluence_score = self._calculate_confluence_score(winning_votes)

        # Calculate average confidence
        average_confidence = self._calculate_average_confidence(winning_votes)

        return VotingResult(
            final_signal=final_signal,
            buy_votes=buy_votes,
            sell_votes=sell_votes,
            neutral_votes=neutral_votes,
            vote_count=vote_count,
            threshold_met=threshold_met,
            confluence_score=confluence_score,
            average_confidence=average_confidence,
        )

    def _determine_signal(
        self,
        buy_votes: List[VoteResult],
        sell_votes: List[VoteResult]
    ) -> Tuple[str, int, bool]:
        """
        Determine the final signal based on votes.

        Args:
            buy_votes: List of buy votes
            sell_votes: List of sell votes

        Returns:
            Tuple of (signal, vote_count, threshold_met)
        """
        buy_count = len(buy_votes)
        sell_count = len(sell_votes)

        # Check if threshold is met
        if buy_count >= self.voting_threshold:
            return 'buy', buy_count, True
        elif sell_count >= self.voting_threshold:
            return 'sell', sell_count, True
        else:
            # No clear signal
            dominant_count = max(buy_count, sell_count)
            return 'wait', dominant_count, False

    def _calculate_confluence_score(
        self,
        votes: List[VoteResult]
    ) -> float:
        """
        Calculate confluence score for winning votes.

        The confluence score (0-100) represents the overall strength
        of the signal based on:
        - Number of votes
        - Average confidence
        - Win rates of voting combinations
        - Risk/reward ratios

        Args:
            votes: List of winning votes

        Returns:
            Confluence score 0-100
        """
        if not votes:
            return 0.0

        # Vote count component (0-40 points)
        # 5 votes = 25, 6 votes = 30, 7 votes = 35, 8 votes = 40
        vote_score = min(len(votes) * 5, 40)

        # Confidence component (0-30 points)
        avg_confidence = sum(v.confidence for v in votes) / len(votes)
        confidence_score = (avg_confidence / 100) * 30

        # Win rate component (0-20 points)
        avg_win_rate = sum(v.win_rate for v in votes) / len(votes)
        win_rate_score = (avg_win_rate / 100) * 20

        # Risk/reward component (0-10 points)
        avg_rr = sum(v.risk_reward for v in votes) / len(votes)
        rr_score = min(avg_rr / 5, 1) * 10  # Max at 5:1 ratio

        total_score = vote_score + confidence_score + win_rate_score + rr_score

        return round(total_score, 2)

    def _calculate_average_confidence(
        self,
        votes: List[VoteResult]
    ) -> float:
        """
        Calculate average confidence of votes.

        Args:
            votes: List of votes

        Returns:
            Average confidence 0-100
        """
        if not votes:
            return 0.0

        return sum(v.confidence for v in votes) / len(votes)

    def get_voting_summary(self, voting_result: VotingResult) -> Dict[str, Any]:
        """
        Get a summary of the voting result.

        Args:
            voting_result: The voting result

        Returns:
            Dictionary with summary information
        """
        return {
            'final_signal': voting_result.final_signal,
            'buy_count': len(voting_result.buy_votes),
            'sell_count': len(voting_result.sell_votes),
            'neutral_count': len(voting_result.neutral_votes),
            'threshold': self.voting_threshold,
            'threshold_met': voting_result.threshold_met,
            'confluence_score': voting_result.confluence_score,
            'average_confidence': voting_result.average_confidence,
            'buy_combinations': [v.display_name for v in voting_result.buy_votes],
            'sell_combinations': [v.display_name for v in voting_result.sell_votes],
        }

    def validate_signal_strength(
        self,
        voting_result: VotingResult,
        min_confluence: float = 50.0,
        min_confidence: float = 60.0
    ) -> Tuple[bool, str]:
        """
        Validate if the signal is strong enough to act on.

        Args:
            voting_result: The voting result to validate
            min_confluence: Minimum confluence score required
            min_confidence: Minimum average confidence required

        Returns:
            Tuple of (is_valid, reason)
        """
        if not voting_result.threshold_met:
            return False, f"Threshold not met: need {self.voting_threshold} votes"

        if voting_result.confluence_score < min_confluence:
            return False, f"Confluence too low: {voting_result.confluence_score} < {min_confluence}"

        if voting_result.average_confidence < min_confidence:
            return False, f"Confidence too low: {voting_result.average_confidence} < {min_confidence}"

        return True, "Signal validated"
