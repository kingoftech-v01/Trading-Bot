"""
Base Combination - Abstract base class for all 8 trading combinations.

Each combination must implement:
- get_name(): Return combination identifier
- get_win_rate(): Expected win rate
- get_risk_reward_ratio(): Expected R:R ratio
- get_required_indicators(): List of needed indicators
- evaluate_buy(): Check buy criteria
- evaluate_sell(): Check sell criteria
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple
import logging

from apps.indicators.services import IndicatorEngine


logger = logging.getLogger('trading_bot')


class BaseCombination(ABC):
    """
    Abstract base class for trading combinations.

    All 8 combinations inherit from this class and implement
    their specific entry/exit logic.
    """

    def __init__(self, indicator_engine: IndicatorEngine = None):
        """
        Initialize combination.

        Args:
            indicator_engine: Optional pre-configured IndicatorEngine
        """
        self.indicator_engine = indicator_engine or IndicatorEngine()
        self.logger = logger

    @abstractmethod
    def get_name(self) -> str:
        """Return the combination name identifier."""
        pass

    @abstractmethod
    def get_display_name(self) -> str:
        """Return human-readable name."""
        pass

    @abstractmethod
    def get_win_rate(self) -> float:
        """Return expected win rate percentage."""
        pass

    @abstractmethod
    def get_risk_reward_ratio(self) -> float:
        """Return expected risk/reward ratio."""
        pass

    @abstractmethod
    def get_required_indicators(self) -> List[str]:
        """Return list of required indicator names."""
        pass

    @abstractmethod
    def evaluate_buy(self, indicators: Dict[str, Any]) -> Tuple[bool, int, Dict]:
        """
        Evaluate BUY criteria.

        Args:
            indicators: Dictionary of calculated indicator values

        Returns:
            Tuple of (signal_valid, confidence_score, criteria_met)
        """
        pass

    @abstractmethod
    def evaluate_sell(self, indicators: Dict[str, Any]) -> Tuple[bool, int, Dict]:
        """
        Evaluate SELL criteria.

        Args:
            indicators: Dictionary of calculated indicator values

        Returns:
            Tuple of (signal_valid, confidence_score, criteria_met)
        """
        pass

    def evaluate(self, ohlcv_data: List[Dict]) -> Dict[str, Any]:
        """
        Main evaluation method.

        Calculates required indicators and evaluates both buy and sell criteria.

        Args:
            ohlcv_data: List of OHLCV dictionaries

        Returns:
            Dictionary with signal, confidence, and details
        """
        # Calculate required indicators
        indicators = self.indicator_engine.calculate_for_combination(
            self.get_name(),
            ohlcv_data
        )

        # Evaluate buy and sell
        buy_valid, buy_confidence, buy_criteria = self.evaluate_buy(indicators)
        sell_valid, sell_confidence, sell_criteria = self.evaluate_sell(indicators)

        # Determine signal
        if buy_valid and buy_confidence >= sell_confidence:
            return {
                'signal': 'buy',
                'confidence': buy_confidence,
                'criteria_met': buy_criteria,
                'indicators': indicators,
                'combination': self.get_name(),
                'win_rate': self.get_win_rate(),
                'risk_reward': self.get_risk_reward_ratio(),
            }
        elif sell_valid and sell_confidence > buy_confidence:
            return {
                'signal': 'sell',
                'confidence': sell_confidence,
                'criteria_met': sell_criteria,
                'indicators': indicators,
                'combination': self.get_name(),
                'win_rate': self.get_win_rate(),
                'risk_reward': self.get_risk_reward_ratio(),
            }
        else:
            return {
                'signal': 'neutral',
                'confidence': 0,
                'criteria_met': {},
                'indicators': indicators,
                'combination': self.get_name(),
                'win_rate': self.get_win_rate(),
                'risk_reward': self.get_risk_reward_ratio(),
            }

    def _calculate_confidence(self, criteria_met: Dict[str, bool]) -> int:
        """
        Calculate confidence score based on criteria met.

        Each criterion contributes equally to the total score.

        Args:
            criteria_met: Dictionary mapping criterion name to boolean

        Returns:
            Confidence score 0-100
        """
        if not criteria_met:
            return 0

        met_count = sum(1 for v in criteria_met.values() if v)
        total_count = len(criteria_met)

        if total_count == 0:
            return 0

        return int((met_count / total_count) * 100)

    def get_description(self) -> str:
        """Return combination description."""
        return f"{self.get_display_name()} - Win Rate: {self.get_win_rate()}%, R:R: {self.get_risk_reward_ratio()}:1"
