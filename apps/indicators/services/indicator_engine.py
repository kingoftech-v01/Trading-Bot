"""
Indicator Engine - Orchestrates all technical indicator calculations.

This is the main entry point for indicator calculations. It manages
all individual indicators and provides a unified interface.
"""

from typing import Dict, Any, List, Optional
import logging

from apps.core.services.base_service import BaseService, ServiceResult
from .rsi import RSIIndicator
from .macd import MACDIndicator
from .adx import ADXIndicator
from .stochastic import StochasticIndicator
from .bollinger_bands import BollingerBandsIndicator
from .linear_regression import LinearRegressionIndicator
from .cci import CCIIndicator
from .atr import ATRIndicator
from .volume_profile import VolumeProfileIndicator
from .support_resistance import SupportResistanceIndicator


logger = logging.getLogger('trading_bot')


class IndicatorEngine(BaseService):
    """
    Main indicator calculation engine.

    Manages all technical indicators and provides:
    - Individual indicator calculations
    - Batch calculations for all indicators
    - Caching of results
    - Custom parameter overrides

    Usage:
        engine = IndicatorEngine()
        result = engine.calculate_all(ohlcv_data)
        rsi = result['rsi']
    """

    # Available indicators
    INDICATOR_CLASSES = {
        'rsi': RSIIndicator,
        'macd': MACDIndicator,
        'adx': ADXIndicator,
        'stochastic': StochasticIndicator,
        'stochastic_slow': StochasticIndicator,
        'bollinger': BollingerBandsIndicator,
        'linear_regression': LinearRegressionIndicator,
        'cci': CCIIndicator,
        'atr': ATRIndicator,
        'volume_profile': VolumeProfileIndicator,
        'support_resistance': SupportResistanceIndicator,
    }

    # Default parameters for slow stochastic
    SLOW_STOCHASTIC_PARAMS = {
        'k_period': 20,
        'k_smooth': 5,
        'd_period': 5,
    }

    def __init__(self, custom_params: Dict[str, Dict] = None):
        """
        Initialize indicator engine.

        Args:
            custom_params: Custom parameters per indicator
                Example: {'rsi': {'period': 21}, 'macd': {'fast_period': 8}}
        """
        super().__init__()
        self.custom_params = custom_params or {}
        self._indicator_cache = {}

    def get_indicator(self, name: str, params: Dict = None) -> Optional[Any]:
        """
        Get or create an indicator instance.

        Args:
            name: Indicator name (e.g., 'rsi', 'macd')
            params: Optional custom parameters

        Returns:
            Indicator instance or None if not found
        """
        if name not in self.INDICATOR_CLASSES:
            self.log_error(f"Unknown indicator: {name}")
            return None

        # Merge parameters
        merged_params = self.custom_params.get(name, {}).copy()
        if params:
            merged_params.update(params)

        # Special handling for slow stochastic
        if name == 'stochastic_slow':
            merged_params = {**self.SLOW_STOCHASTIC_PARAMS, **merged_params}

        indicator_class = self.INDICATOR_CLASSES[name]
        return indicator_class(merged_params)

    def calculate(
        self,
        indicator_name: str,
        ohlcv_data: List[Dict],
        params: Dict = None
    ) -> Dict[str, Any]:
        """
        Calculate a single indicator.

        Args:
            indicator_name: Name of the indicator
            ohlcv_data: List of OHLCV dictionaries
            params: Optional custom parameters

        Returns:
            Dictionary of calculated values
        """
        indicator = self.get_indicator(indicator_name, params)
        if not indicator:
            return {}

        try:
            return indicator.calculate(ohlcv_data)
        except Exception as e:
            self.log_error(f"Error calculating {indicator_name}: {str(e)}", exc=e)
            return {}

    def calculate_all(
        self,
        ohlcv_data: List[Dict],
        indicators: List[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate multiple indicators at once.

        Args:
            ohlcv_data: List of OHLCV dictionaries
            indicators: List of indicator names to calculate
                       If None, calculates all indicators

        Returns:
            Dictionary mapping indicator names to their values
        """
        if indicators is None:
            indicators = list(self.INDICATOR_CLASSES.keys())

        results = {}

        for indicator_name in indicators:
            results[indicator_name] = self.calculate(indicator_name, ohlcv_data)

        # Add current close price for convenience
        if ohlcv_data:
            results['current_close'] = float(ohlcv_data[-1].get('close', 0))
            results['current_timestamp'] = ohlcv_data[-1].get('timestamp')

        return results

    def calculate_for_combination(
        self,
        combination_name: str,
        ohlcv_data: List[Dict]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate indicators required for a specific combination.

        Args:
            combination_name: Name of the trading combination
            ohlcv_data: List of OHLCV dictionaries

        Returns:
            Dictionary of required indicator values
        """
        # Map combinations to required indicators
        combination_indicators = {
            'golden_confluence': [
                'rsi', 'macd', 'adx', 'stochastic', 'bollinger'
            ],
            'mean_reversion': [
                'rsi', 'stochastic', 'bollinger', 'macd', 'atr'
            ],
            'breakout_momentum': [
                'bollinger', 'adx', 'rsi', 'volume_profile', 'linear_regression'
            ],
            'harmonic_confluence': [
                'rsi', 'macd', 'linear_regression', 'stochastic', 'volume_profile'
            ],
            'linear_regression_channel': [
                'linear_regression', 'rsi', 'adx', 'bollinger', 'cci'
            ],
            'multi_timeframe': [
                'adx', 'linear_regression', 'rsi', 'macd', 'stochastic',
                'bollinger', 'volume_profile'
            ],
            'stochastic_crossover': [
                'stochastic', 'stochastic_slow', 'rsi', 'volume_profile',
                'support_resistance'
            ],
            'ultimate_confluence': [
                'rsi', 'macd', 'adx', 'stochastic', 'bollinger',
                'linear_regression', 'volume_profile', 'cci', 'atr'
            ],
        }

        indicators = combination_indicators.get(combination_name, [])
        return self.calculate_all(ohlcv_data, indicators)

    def get_signal_summary(
        self,
        ohlcv_data: List[Dict]
    ) -> Dict[str, str]:
        """
        Get signal summary from all indicators.

        Returns:
            Dictionary mapping indicator names to their signals
        """
        signals = {}
        results = self.calculate_all(ohlcv_data)

        for name, values in results.items():
            if name in ['current_close', 'current_timestamp']:
                continue

            indicator = self.get_indicator(name)
            if indicator and values:
                try:
                    signals[name] = indicator.get_signal(values)
                except Exception:
                    signals[name] = 'neutral'

        return signals

    def calculate_confluence_score(
        self,
        ohlcv_data: List[Dict],
        direction: str = 'buy'
    ) -> int:
        """
        Calculate overall confluence score (0-100).

        Based on how many indicators agree on the direction.

        Args:
            ohlcv_data: List of OHLCV dictionaries
            direction: 'buy' or 'sell'

        Returns:
            Confluence score 0-100
        """
        signals = self.get_signal_summary(ohlcv_data)

        # Count agreeing signals
        agreeing = sum(1 for s in signals.values() if s == direction)
        total = len([s for s in signals.values() if s != 'neutral'])

        if total == 0:
            return 0

        return int((agreeing / total) * 100)
