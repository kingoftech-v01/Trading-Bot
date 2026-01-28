"""
Multi-Pair Validator - Validates signals across correlated pairs.

Provides additional confirmation by checking if correlated
trading pairs show similar signals.
"""

from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import logging

from apps.core.services.base_service import BaseService, ServiceResult
from apps.market_data.models import TradingPair, CorrelationMatrix


logger = logging.getLogger('trading_bot')


class MultiPairValidator(BaseService):
    """
    Validates signals by checking correlated pairs.

    When a signal is generated for one pair, this validator
    checks if correlated pairs show similar signals, providing
    additional confidence in the trade setup.

    Correlation Thresholds:
    - Strong positive correlation: > 0.7
    - Strong negative correlation: < -0.7
    - Weak correlation: -0.3 to 0.3 (ignored)
    """

    STRONG_POSITIVE_CORRELATION = 0.7
    STRONG_NEGATIVE_CORRELATION = -0.7
    MIN_CONFIRMATIONS_REQUIRED = 1

    def __init__(self, signal_generator=None):
        """
        Initialize the validator.

        Args:
            signal_generator: Optional SignalGenerator for evaluating pairs
        """
        super().__init__()
        self.signal_generator = signal_generator

    def validate_with_correlations(
        self,
        primary_pair: TradingPair,
        primary_signal: str,
        timeframe: str = '1h',
    ) -> ServiceResult:
        """
        Validate a signal by checking correlated pairs.

        Args:
            primary_pair: The main trading pair
            primary_signal: The signal to validate ('buy' or 'sell')
            timeframe: Timeframe for analysis

        Returns:
            ServiceResult with validation details
        """
        try:
            # Get correlated pairs
            correlations = self._get_correlated_pairs(primary_pair)

            if not correlations:
                return self.success_result({
                    'validated': True,
                    'reason': 'No correlated pairs to validate against',
                    'confirmations': 0,
                    'contradictions': 0,
                })

            confirmations = []
            contradictions = []
            neutral = []

            for corr_data in correlations:
                correlated_pair = corr_data['pair']
                correlation = corr_data['correlation']

                # Get signal for correlated pair
                corr_signal = self._get_pair_signal(correlated_pair, timeframe)

                # Determine if it confirms or contradicts
                result = self._evaluate_correlation(
                    primary_signal,
                    corr_signal,
                    correlation,
                )

                if result == 'confirm':
                    confirmations.append({
                        'pair': correlated_pair.symbol,
                        'correlation': correlation,
                        'signal': corr_signal,
                    })
                elif result == 'contradict':
                    contradictions.append({
                        'pair': correlated_pair.symbol,
                        'correlation': correlation,
                        'signal': corr_signal,
                    })
                else:
                    neutral.append({
                        'pair': correlated_pair.symbol,
                        'correlation': correlation,
                        'signal': corr_signal,
                    })

            # Determine validation result
            is_validated = len(confirmations) >= self.MIN_CONFIRMATIONS_REQUIRED
            confidence_boost = self._calculate_confidence_boost(
                confirmations, contradictions
            )

            return self.success_result({
                'validated': is_validated,
                'confirmations': len(confirmations),
                'contradictions': len(contradictions),
                'neutral': len(neutral),
                'confidence_boost': confidence_boost,
                'details': {
                    'confirming_pairs': confirmations,
                    'contradicting_pairs': contradictions,
                    'neutral_pairs': neutral,
                },
            })

        except Exception as e:
            self.log_error(f"Error validating correlations: {str(e)}", exc=e)
            return self.error_result(str(e))

    def _get_correlated_pairs(
        self,
        primary_pair: TradingPair
    ) -> List[Dict[str, Any]]:
        """
        Get pairs that are correlated with the primary pair.

        Args:
            primary_pair: The main trading pair

        Returns:
            List of correlated pairs with correlation values
        """
        correlations = []

        # Check as pair1
        matrix_entries = CorrelationMatrix.objects.filter(
            pair1=primary_pair,
            is_active=True,
        ).select_related('pair2')

        for entry in matrix_entries:
            if abs(entry.correlation) > abs(self.STRONG_NEGATIVE_CORRELATION):
                correlations.append({
                    'pair': entry.pair2,
                    'correlation': float(entry.correlation),
                })

        # Check as pair2
        matrix_entries = CorrelationMatrix.objects.filter(
            pair2=primary_pair,
            is_active=True,
        ).select_related('pair1')

        for entry in matrix_entries:
            if abs(entry.correlation) > abs(self.STRONG_NEGATIVE_CORRELATION):
                correlations.append({
                    'pair': entry.pair1,
                    'correlation': float(entry.correlation),
                })

        return correlations

    def _get_pair_signal(
        self,
        trading_pair: TradingPair,
        timeframe: str
    ) -> str:
        """
        Get the current signal for a trading pair.

        Uses the most recent signal session if available.
        """
        from ..models import SignalSession

        # Get most recent session
        session = SignalSession.objects.filter(
            trading_pair=trading_pair,
            timeframe=timeframe,
        ).order_by('-evaluated_at').first()

        if session:
            return session.final_signal

        return 'wait'

    def _evaluate_correlation(
        self,
        primary_signal: str,
        correlated_signal: str,
        correlation: float
    ) -> str:
        """
        Evaluate if correlated pair confirms or contradicts.

        For positive correlation:
        - Same signal = confirm
        - Opposite signal = contradict

        For negative correlation:
        - Opposite signal = confirm
        - Same signal = contradict

        Args:
            primary_signal: Signal for primary pair
            correlated_signal: Signal for correlated pair
            correlation: Correlation coefficient

        Returns:
            'confirm', 'contradict', or 'neutral'
        """
        if correlated_signal == 'wait':
            return 'neutral'

        is_positive_correlation = correlation > 0

        # Same direction check
        same_direction = primary_signal == correlated_signal

        if is_positive_correlation:
            # Positive correlation: expect same direction
            if same_direction:
                return 'confirm'
            else:
                return 'contradict'
        else:
            # Negative correlation: expect opposite direction
            if not same_direction:
                return 'confirm'
            else:
                return 'contradict'

    def _calculate_confidence_boost(
        self,
        confirmations: List[Dict],
        contradictions: List[Dict]
    ) -> float:
        """
        Calculate confidence boost from correlations.

        Args:
            confirmations: List of confirming pairs
            contradictions: List of contradicting pairs

        Returns:
            Confidence boost percentage (-10 to +10)
        """
        if not confirmations and not contradictions:
            return 0.0

        # Each confirmation adds 2%, each contradiction subtracts 3%
        boost = len(confirmations) * 2.0 - len(contradictions) * 3.0

        # Clamp to -10 to +10
        return max(-10.0, min(10.0, boost))

    def get_correlation_summary(
        self,
        trading_pair: TradingPair
    ) -> Dict[str, Any]:
        """
        Get a summary of all correlations for a pair.

        Args:
            trading_pair: The trading pair

        Returns:
            Summary of correlations
        """
        correlations = self._get_correlated_pairs(trading_pair)

        positive_correlations = [
            c for c in correlations if c['correlation'] > 0
        ]
        negative_correlations = [
            c for c in correlations if c['correlation'] < 0
        ]

        return {
            'total_correlated_pairs': len(correlations),
            'positive_correlations': len(positive_correlations),
            'negative_correlations': len(negative_correlations),
            'strongest_positive': max(
                (c['correlation'] for c in positive_correlations),
                default=0
            ),
            'strongest_negative': min(
                (c['correlation'] for c in negative_correlations),
                default=0
            ),
            'pairs': [
                {
                    'symbol': c['pair'].symbol,
                    'correlation': c['correlation'],
                }
                for c in correlations
            ],
        }
