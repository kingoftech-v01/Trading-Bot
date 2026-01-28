"""
Base Indicator - Abstract base class for all technical indicators.

All indicators inherit from this class and implement:
- default_params(): Default calculation parameters
- calculate(): Core calculation logic
- get_signal(): Signal interpretation
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import numpy as np
import logging

logger = logging.getLogger('trading_bot')


class BaseIndicator(ABC):
    """
    Abstract base class for technical indicators.

    All indicators must implement:
    - default_params(): Return default parameters
    - calculate(): Perform the calculation
    - get_signal(): Interpret values as buy/sell/neutral

    Usage:
        indicator = RSIIndicator({'period': 14})
        result = indicator.calculate(ohlcv_data)
        signal = indicator.get_signal(result)
    """

    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize indicator with optional custom parameters.

        Args:
            params: Custom parameters (merged with defaults)
        """
        self.params = self.default_params()
        if params:
            self.params.update(params)
        self.logger = logger

    @abstractmethod
    def default_params(self) -> Dict[str, Any]:
        """
        Return default parameters for this indicator.

        Returns:
            Dictionary of parameter names and default values
        """
        pass

    @abstractmethod
    def calculate(self, ohlcv_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate indicator values from OHLCV data.

        Args:
            ohlcv_data: List of OHLCV dictionaries with keys:
                - timestamp: datetime
                - open: float
                - high: float
                - low: float
                - close: float
                - volume: float

        Returns:
            Dictionary of calculated values
        """
        pass

    @abstractmethod
    def get_signal(self, values: Dict[str, Any]) -> str:
        """
        Interpret calculated values as a trading signal.

        Args:
            values: Dictionary of calculated indicator values

        Returns:
            'buy', 'sell', or 'neutral'
        """
        pass

    def get_name(self) -> str:
        """Return the indicator name."""
        return self.__class__.__name__.replace('Indicator', '').lower()

    def _extract_prices(
        self,
        ohlcv_data: List[Dict[str, Any]],
        price_type: str = 'close'
    ) -> np.ndarray:
        """
        Extract price array from OHLCV data.

        Args:
            ohlcv_data: List of OHLCV dictionaries
            price_type: 'open', 'high', 'low', 'close'

        Returns:
            NumPy array of prices
        """
        return np.array([float(d[price_type]) for d in ohlcv_data])

    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """
        Calculate Exponential Moving Average.

        Args:
            data: Price data
            period: EMA period

        Returns:
            NumPy array of EMA values
        """
        alpha = 2 / (period + 1)
        ema = np.zeros_like(data)
        ema[:period] = np.nan

        # Initialize with SMA
        ema[period - 1] = np.mean(data[:period])

        # Calculate EMA
        for i in range(period, len(data)):
            ema[i] = data[i] * alpha + ema[i - 1] * (1 - alpha)

        return ema

    def _sma(self, data: np.ndarray, period: int) -> np.ndarray:
        """
        Calculate Simple Moving Average.

        Args:
            data: Price data
            period: SMA period

        Returns:
            NumPy array of SMA values
        """
        sma = np.zeros_like(data)
        sma[:period - 1] = np.nan

        for i in range(period - 1, len(data)):
            sma[i] = np.mean(data[i - period + 1:i + 1])

        return sma

    def _true_range(self, ohlcv_data: List[Dict[str, Any]]) -> np.ndarray:
        """
        Calculate True Range.

        TR = max(high - low, |high - prev_close|, |low - prev_close|)

        Args:
            ohlcv_data: List of OHLCV dictionaries

        Returns:
            NumPy array of True Range values
        """
        highs = self._extract_prices(ohlcv_data, 'high')
        lows = self._extract_prices(ohlcv_data, 'low')
        closes = self._extract_prices(ohlcv_data, 'close')

        tr = np.zeros(len(ohlcv_data))
        tr[0] = highs[0] - lows[0]

        for i in range(1, len(ohlcv_data)):
            hl = highs[i] - lows[i]
            hpc = abs(highs[i] - closes[i - 1])
            lpc = abs(lows[i] - closes[i - 1])
            tr[i] = max(hl, hpc, lpc)

        return tr

    def _validate_data(self, ohlcv_data: List[Dict[str, Any]], min_periods: int) -> bool:
        """
        Validate that we have enough data for calculation.

        Args:
            ohlcv_data: List of OHLCV dictionaries
            min_periods: Minimum required periods

        Returns:
            True if valid, False otherwise
        """
        if not ohlcv_data:
            return False
        if len(ohlcv_data) < min_periods:
            self.logger.warning(
                f"{self.get_name()}: Insufficient data. "
                f"Got {len(ohlcv_data)}, need {min_periods}"
            )
            return False
        return True
