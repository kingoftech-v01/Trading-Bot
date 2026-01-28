"""
Confluence Scorer - Calculates detailed confluence scores.

Provides a comprehensive scoring system to evaluate
the strength and reliability of trading signals.
"""

from typing import Dict, Any, List
from dataclasses import dataclass
import logging

from apps.core.services.base_service import BaseService
from .voting_system import VotingResult, VoteResult


logger = logging.getLogger('trading_bot')


@dataclass
class ScoreComponent:
    """Individual score component."""
    name: str
    score: float
    max_score: float
    weight: float
    details: Dict[str, Any]


class ConfluenceScorer(BaseService):
    """
    Calculates detailed confluence scores for signals.

    The confluence score represents the overall strength and
    reliability of a trading signal based on multiple factors:

    1. Vote Weight (40%): Number of combinations agreeing
    2. Confidence (25%): Average confidence of votes
    3. Win Rate (20%): Historical win rates of voting combinations
    4. Risk/Reward (10%): Risk/reward ratios of combinations
    5. Indicator Alignment (5%): How well indicators align

    Total score: 0-100
    """

    # Scoring weights
    VOTE_WEIGHT = 0.40
    CONFIDENCE_WEIGHT = 0.25
    WIN_RATE_WEIGHT = 0.20
    RISK_REWARD_WEIGHT = 0.10
    ALIGNMENT_WEIGHT = 0.05

    # Thresholds
    MIN_SCORE_FOR_SIGNAL = 50.0
    STRONG_SIGNAL_THRESHOLD = 70.0
    EXCELLENT_SIGNAL_THRESHOLD = 85.0

    def calculate_detailed_score(
        self,
        voting_result: VotingResult
    ) -> Dict[str, Any]:
        """
        Calculate detailed confluence score breakdown.

        Args:
            voting_result: The voting result to score

        Returns:
            Dictionary with detailed scoring breakdown
        """
        # Get winning votes
        if voting_result.final_signal == 'buy':
            winning_votes = voting_result.buy_votes
        elif voting_result.final_signal == 'sell':
            winning_votes = voting_result.sell_votes
        else:
            winning_votes = []

        # Calculate each component
        vote_component = self._calculate_vote_score(winning_votes)
        confidence_component = self._calculate_confidence_score(winning_votes)
        win_rate_component = self._calculate_win_rate_score(winning_votes)
        rr_component = self._calculate_risk_reward_score(winning_votes)
        alignment_component = self._calculate_alignment_score(
            voting_result, winning_votes
        )

        # Calculate total weighted score
        total_score = (
            vote_component.score * self.VOTE_WEIGHT +
            confidence_component.score * self.CONFIDENCE_WEIGHT +
            win_rate_component.score * self.WIN_RATE_WEIGHT +
            rr_component.score * self.RISK_REWARD_WEIGHT +
            alignment_component.score * self.ALIGNMENT_WEIGHT
        )

        # Determine signal strength category
        strength_category = self._get_strength_category(total_score)

        return {
            'total_score': round(total_score, 2),
            'strength_category': strength_category,
            'vote_weight_score': round(vote_component.score * self.VOTE_WEIGHT, 2),
            'confidence_score': round(confidence_component.score * self.CONFIDENCE_WEIGHT, 2),
            'win_rate_score': round(win_rate_component.score * self.WIN_RATE_WEIGHT, 2),
            'risk_reward_score': round(rr_component.score * self.RISK_REWARD_WEIGHT, 2),
            'indicator_alignment_score': round(alignment_component.score * self.ALIGNMENT_WEIGHT, 2),
            'components': {
                'vote_weight': {
                    'raw_score': vote_component.score,
                    'weighted_score': vote_component.score * self.VOTE_WEIGHT,
                    'details': vote_component.details,
                },
                'confidence': {
                    'raw_score': confidence_component.score,
                    'weighted_score': confidence_component.score * self.CONFIDENCE_WEIGHT,
                    'details': confidence_component.details,
                },
                'win_rate': {
                    'raw_score': win_rate_component.score,
                    'weighted_score': win_rate_component.score * self.WIN_RATE_WEIGHT,
                    'details': win_rate_component.details,
                },
                'risk_reward': {
                    'raw_score': rr_component.score,
                    'weighted_score': rr_component.score * self.RISK_REWARD_WEIGHT,
                    'details': rr_component.details,
                },
                'alignment': {
                    'raw_score': alignment_component.score,
                    'weighted_score': alignment_component.score * self.ALIGNMENT_WEIGHT,
                    'details': alignment_component.details,
                },
            },
            'voting_combinations': [v.display_name for v in winning_votes],
            'is_actionable': total_score >= self.MIN_SCORE_FOR_SIGNAL,
        }

    def _calculate_vote_score(self, votes: List[VoteResult]) -> ScoreComponent:
        """
        Calculate vote weight score.

        Scoring:
        - 5 votes: 62.5 points
        - 6 votes: 75 points
        - 7 votes: 87.5 points
        - 8 votes: 100 points
        """
        vote_count = len(votes)
        # Linear scale from 5 votes (62.5) to 8 votes (100)
        if vote_count >= 5:
            score = 62.5 + (vote_count - 5) * 12.5
        else:
            score = vote_count * 12.5

        score = min(score, 100)

        return ScoreComponent(
            name='vote_weight',
            score=score,
            max_score=100,
            weight=self.VOTE_WEIGHT,
            details={
                'vote_count': vote_count,
                'threshold': 5,
                'max_votes': 8,
            }
        )

    def _calculate_confidence_score(
        self,
        votes: List[VoteResult]
    ) -> ScoreComponent:
        """
        Calculate confidence score.

        Based on average confidence of voting combinations.
        """
        if not votes:
            return ScoreComponent(
                name='confidence',
                score=0,
                max_score=100,
                weight=self.CONFIDENCE_WEIGHT,
                details={'average_confidence': 0, 'min': 0, 'max': 0}
            )

        confidences = [v.confidence for v in votes]
        avg_confidence = sum(confidences) / len(confidences)
        min_confidence = min(confidences)
        max_confidence = max(confidences)

        # Score is directly the average confidence
        score = avg_confidence

        return ScoreComponent(
            name='confidence',
            score=score,
            max_score=100,
            weight=self.CONFIDENCE_WEIGHT,
            details={
                'average_confidence': round(avg_confidence, 2),
                'min_confidence': min_confidence,
                'max_confidence': max_confidence,
                'individual': {v.combination_name: v.confidence for v in votes},
            }
        )

    def _calculate_win_rate_score(
        self,
        votes: List[VoteResult]
    ) -> ScoreComponent:
        """
        Calculate win rate score.

        Based on historical win rates of voting combinations.
        Higher win rates = higher score.
        """
        if not votes:
            return ScoreComponent(
                name='win_rate',
                score=0,
                max_score=100,
                weight=self.WIN_RATE_WEIGHT,
                details={'average_win_rate': 0}
            )

        win_rates = [v.win_rate for v in votes]
        avg_win_rate = sum(win_rates) / len(win_rates)

        # Score based on average win rate
        # 50% win rate = 50 points, 70% = 100 points
        # Linear interpolation
        score = min((avg_win_rate - 50) * (100 / 20) + 50, 100)
        score = max(score, 0)

        return ScoreComponent(
            name='win_rate',
            score=score,
            max_score=100,
            weight=self.WIN_RATE_WEIGHT,
            details={
                'average_win_rate': round(avg_win_rate, 2),
                'min_win_rate': min(win_rates),
                'max_win_rate': max(win_rates),
                'individual': {v.combination_name: v.win_rate for v in votes},
            }
        )

    def _calculate_risk_reward_score(
        self,
        votes: List[VoteResult]
    ) -> ScoreComponent:
        """
        Calculate risk/reward score.

        Higher R:R ratios = higher score.
        Target: 3:1 minimum
        """
        if not votes:
            return ScoreComponent(
                name='risk_reward',
                score=0,
                max_score=100,
                weight=self.RISK_REWARD_WEIGHT,
                details={'average_rr': 0}
            )

        rr_ratios = [v.risk_reward for v in votes]
        avg_rr = sum(rr_ratios) / len(rr_ratios)

        # Score based on average R:R
        # 3:1 = 75 points, 4:1 = 87.5 points, 5:1+ = 100 points
        score = min(avg_rr * 25, 100)

        return ScoreComponent(
            name='risk_reward',
            score=score,
            max_score=100,
            weight=self.RISK_REWARD_WEIGHT,
            details={
                'average_rr': round(avg_rr, 2),
                'min_rr': min(rr_ratios),
                'max_rr': max(rr_ratios),
                'individual': {v.combination_name: v.risk_reward for v in votes},
            }
        )

    def _calculate_alignment_score(
        self,
        voting_result: VotingResult,
        winning_votes: List[VoteResult]
    ) -> ScoreComponent:
        """
        Calculate indicator alignment score.

        Measures how well the votes align without conflicting signals.
        """
        total_votes = (
            len(voting_result.buy_votes) +
            len(voting_result.sell_votes) +
            len(voting_result.neutral_votes)
        )

        if total_votes == 0:
            return ScoreComponent(
                name='alignment',
                score=0,
                max_score=100,
                weight=self.ALIGNMENT_WEIGHT,
                details={'alignment_ratio': 0}
            )

        winning_count = len(winning_votes)

        # Opposing votes reduce the score
        if voting_result.final_signal == 'buy':
            opposing_count = len(voting_result.sell_votes)
        elif voting_result.final_signal == 'sell':
            opposing_count = len(voting_result.buy_votes)
        else:
            opposing_count = max(
                len(voting_result.buy_votes),
                len(voting_result.sell_votes)
            )

        # Score based on ratio of winning to opposing
        if opposing_count == 0:
            alignment_ratio = 1.0
        else:
            alignment_ratio = winning_count / (winning_count + opposing_count)

        score = alignment_ratio * 100

        return ScoreComponent(
            name='alignment',
            score=score,
            max_score=100,
            weight=self.ALIGNMENT_WEIGHT,
            details={
                'alignment_ratio': round(alignment_ratio, 2),
                'winning_count': winning_count,
                'opposing_count': opposing_count,
                'neutral_count': len(voting_result.neutral_votes),
            }
        )

    def _get_strength_category(self, score: float) -> str:
        """
        Get signal strength category.

        Args:
            score: Total confluence score

        Returns:
            Strength category string
        """
        if score >= self.EXCELLENT_SIGNAL_THRESHOLD:
            return 'excellent'
        elif score >= self.STRONG_SIGNAL_THRESHOLD:
            return 'strong'
        elif score >= self.MIN_SCORE_FOR_SIGNAL:
            return 'moderate'
        elif score >= 30:
            return 'weak'
        else:
            return 'none'

    def get_scoring_thresholds(self) -> Dict[str, float]:
        """Get all scoring thresholds."""
        return {
            'min_for_signal': self.MIN_SCORE_FOR_SIGNAL,
            'strong_signal': self.STRONG_SIGNAL_THRESHOLD,
            'excellent_signal': self.EXCELLENT_SIGNAL_THRESHOLD,
        }
