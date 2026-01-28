"""
Combination Evaluator - Orchestrates evaluation of all 8 combinations.

This is the main entry point for evaluating trading combinations
and collecting votes for the signal generation system.
"""

from typing import Dict, Any, List
import logging

from apps.core.services.base_service import BaseService, ServiceResult
from apps.indicators.services import IndicatorEngine
from .golden_confluence import GoldenConfluence
from .mean_reversion import MeanReversion
from .breakout_momentum import BreakoutMomentum
from .harmonic_confluence import HarmonicConfluence
from .linear_regression_channel import LinearRegressionChannel
from .multi_timeframe import MultiTimeframe
from .stochastic_crossover import StochasticCrossover
from .ultimate_confluence import UltimateConfluence


logger = logging.getLogger('trading_bot')


class CombinationEvaluator(BaseService):
    """
    Evaluates all 8 trading combinations for a given dataset.

    This service is used by the signals app to collect votes
    from each combination and determine the final signal.
    """

    def __init__(self, indicator_engine: IndicatorEngine = None):
        """
        Initialize evaluator with all 8 combinations.

        Args:
            indicator_engine: Optional shared IndicatorEngine
        """
        super().__init__()
        self.indicator_engine = indicator_engine or IndicatorEngine()

        # Initialize all combinations
        self.combinations = [
            GoldenConfluence(self.indicator_engine),
            MeanReversion(self.indicator_engine),
            BreakoutMomentum(self.indicator_engine),
            HarmonicConfluence(self.indicator_engine),
            LinearRegressionChannel(self.indicator_engine),
            MultiTimeframe(self.indicator_engine),
            StochasticCrossover(self.indicator_engine),
            UltimateConfluence(self.indicator_engine),
        ]

    def evaluate_all(self, ohlcv_data: List[Dict]) -> Dict[str, Any]:
        """
        Evaluate all 8 combinations.

        Args:
            ohlcv_data: List of OHLCV dictionaries

        Returns:
            Dictionary with results from all combinations
        """
        results = {
            'buy_votes': [],
            'sell_votes': [],
            'neutral_votes': [],
            'details': {},
        }

        for combination in self.combinations:
            try:
                result = combination.evaluate(ohlcv_data)
                signal = result['signal']

                # Categorize vote
                vote_info = {
                    'combination': combination.get_name(),
                    'display_name': combination.get_display_name(),
                    'signal': signal,
                    'confidence': result['confidence'],
                    'win_rate': combination.get_win_rate(),
                    'risk_reward': combination.get_risk_reward_ratio(),
                    'criteria_met': result['criteria_met'],
                }

                if signal == 'buy':
                    results['buy_votes'].append(vote_info)
                elif signal == 'sell':
                    results['sell_votes'].append(vote_info)
                else:
                    results['neutral_votes'].append(vote_info)

                results['details'][combination.get_name()] = result

            except Exception as e:
                self.log_error(
                    f"Error evaluating {combination.get_name()}: {str(e)}",
                    exc=e
                )
                results['neutral_votes'].append({
                    'combination': combination.get_name(),
                    'display_name': combination.get_display_name(),
                    'signal': 'error',
                    'confidence': 0,
                    'error': str(e),
                })

        # Calculate summary
        results['summary'] = {
            'total_combinations': len(self.combinations),
            'buy_count': len(results['buy_votes']),
            'sell_count': len(results['sell_votes']),
            'neutral_count': len(results['neutral_votes']),
        }

        return results

    def get_combination_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all combinations.

        Returns:
            List of combination info dictionaries
        """
        return [
            {
                'name': c.get_name(),
                'display_name': c.get_display_name(),
                'win_rate': c.get_win_rate(),
                'risk_reward': c.get_risk_reward_ratio(),
                'required_indicators': c.get_required_indicators(),
                'description': c.get_description(),
            }
            for c in self.combinations
        ]

    def evaluate_single(
        self,
        combination_name: str,
        ohlcv_data: List[Dict]
    ) -> Dict[str, Any]:
        """
        Evaluate a single combination.

        Args:
            combination_name: Name of the combination
            ohlcv_data: List of OHLCV dictionaries

        Returns:
            Evaluation result or None if not found
        """
        for combination in self.combinations:
            if combination.get_name() == combination_name:
                return combination.evaluate(ohlcv_data)

        self.log_error(f"Combination not found: {combination_name}")
        return None
