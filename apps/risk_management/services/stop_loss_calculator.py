"""
Stop Loss Calculator - Determines optimal stop loss levels.

Provides multiple methods for stop loss placement:
- ATR-based
- Percentage-based
- Support/Resistance-based
- Fixed points
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
import logging

from apps.core.services.base_service import BaseService, ServiceResult


logger = logging.getLogger('trading_bot')


class StopLossCalculator(BaseService):
    """
    Calculates stop loss levels using various methods.

    Methods:
    1. ATR-based: Uses Average True Range for volatility-based stops
    2. Percentage: Fixed percentage from entry
    3. Support/Resistance: Based on key levels
    4. Swing: Based on recent swing highs/lows
    """

    # Default multipliers
    DEFAULT_ATR_MULTIPLIER = 2.0
    DEFAULT_PERCENTAGE = 0.02  # 2%

    def calculate_atr_based(
        self,
        entry_price: Decimal,
        atr: Decimal,
        direction: str = 'buy',
        multiplier: float = None,
    ) -> ServiceResult:
        """
        Calculate ATR-based stop loss.

        Args:
            entry_price: Entry price
            atr: Average True Range value
            direction: 'buy' or 'sell'
            multiplier: ATR multiplier (default: 2.0)

        Returns:
            ServiceResult with stop loss data
        """
        try:
            entry_price = Decimal(str(entry_price))
            atr = Decimal(str(atr))
            multiplier = Decimal(str(multiplier or self.DEFAULT_ATR_MULTIPLIER))

            sl_distance = atr * multiplier

            if direction == 'buy':
                stop_loss = entry_price - sl_distance
            else:
                stop_loss = entry_price + sl_distance

            sl_percent = (sl_distance / entry_price) * 100

            return self.success_result({
                'stop_loss': float(stop_loss),
                'entry_price': float(entry_price),
                'sl_distance': float(sl_distance),
                'sl_percent': float(sl_percent),
                'atr': float(atr),
                'multiplier': float(multiplier),
                'method': 'atr',
                'direction': direction,
            })

        except Exception as e:
            self.log_error(f"Error calculating ATR SL: {str(e)}", exc=e)
            return self.error_result(str(e))

    def calculate_percentage_based(
        self,
        entry_price: Decimal,
        direction: str = 'buy',
        percentage: float = None,
    ) -> ServiceResult:
        """
        Calculate percentage-based stop loss.

        Args:
            entry_price: Entry price
            direction: 'buy' or 'sell'
            percentage: Stop loss percentage (default: 2%)

        Returns:
            ServiceResult with stop loss data
        """
        try:
            entry_price = Decimal(str(entry_price))
            percentage = Decimal(str(percentage or self.DEFAULT_PERCENTAGE))

            sl_distance = entry_price * percentage

            if direction == 'buy':
                stop_loss = entry_price - sl_distance
            else:
                stop_loss = entry_price + sl_distance

            return self.success_result({
                'stop_loss': float(stop_loss),
                'entry_price': float(entry_price),
                'sl_distance': float(sl_distance),
                'sl_percent': float(percentage * 100),
                'method': 'percentage',
                'direction': direction,
            })

        except Exception as e:
            self.log_error(f"Error calculating percentage SL: {str(e)}", exc=e)
            return self.error_result(str(e))

    def calculate_support_resistance_based(
        self,
        entry_price: Decimal,
        direction: str = 'buy',
        support: Decimal = None,
        resistance: Decimal = None,
        buffer_percent: float = 0.001,
    ) -> ServiceResult:
        """
        Calculate support/resistance-based stop loss.

        Args:
            entry_price: Entry price
            direction: 'buy' or 'sell'
            support: Support level (for buys)
            resistance: Resistance level (for sells)
            buffer_percent: Buffer below/above level

        Returns:
            ServiceResult with stop loss data
        """
        try:
            entry_price = Decimal(str(entry_price))
            buffer_percent = Decimal(str(buffer_percent))

            if direction == 'buy':
                if support is None:
                    return self.error_result("Support level required for buy orders")

                support = Decimal(str(support))
                buffer = support * buffer_percent
                stop_loss = support - buffer

            else:  # sell
                if resistance is None:
                    return self.error_result("Resistance level required for sell orders")

                resistance = Decimal(str(resistance))
                buffer = resistance * buffer_percent
                stop_loss = resistance + buffer

            sl_distance = abs(entry_price - stop_loss)
            sl_percent = (sl_distance / entry_price) * 100

            return self.success_result({
                'stop_loss': float(stop_loss),
                'entry_price': float(entry_price),
                'sl_distance': float(sl_distance),
                'sl_percent': float(sl_percent),
                'support': float(support) if support else None,
                'resistance': float(resistance) if resistance else None,
                'buffer_percent': float(buffer_percent * 100),
                'method': 'support_resistance',
                'direction': direction,
            })

        except Exception as e:
            self.log_error(f"Error calculating S/R SL: {str(e)}", exc=e)
            return self.error_result(str(e))

    def calculate_swing_based(
        self,
        entry_price: Decimal,
        ohlcv_data: List[Dict],
        direction: str = 'buy',
        lookback: int = 20,
        buffer_percent: float = 0.001,
    ) -> ServiceResult:
        """
        Calculate swing-based stop loss.

        Uses recent swing low (for buys) or swing high (for sells).

        Args:
            entry_price: Entry price
            ohlcv_data: OHLCV data for swing detection
            direction: 'buy' or 'sell'
            lookback: Number of candles to look back
            buffer_percent: Buffer beyond swing point

        Returns:
            ServiceResult with stop loss data
        """
        try:
            entry_price = Decimal(str(entry_price))
            buffer_percent = Decimal(str(buffer_percent))

            if len(ohlcv_data) < lookback:
                return self.error_result(
                    f"Not enough data: {len(ohlcv_data)} < {lookback}"
                )

            recent_data = ohlcv_data[-lookback:]

            if direction == 'buy':
                # Find lowest low
                swing_low = min(Decimal(str(d['low'])) for d in recent_data)
                buffer = swing_low * buffer_percent
                stop_loss = swing_low - buffer
                swing_point = swing_low
            else:
                # Find highest high
                swing_high = max(Decimal(str(d['high'])) for d in recent_data)
                buffer = swing_high * buffer_percent
                stop_loss = swing_high + buffer
                swing_point = swing_high

            sl_distance = abs(entry_price - stop_loss)
            sl_percent = (sl_distance / entry_price) * 100

            return self.success_result({
                'stop_loss': float(stop_loss),
                'entry_price': float(entry_price),
                'sl_distance': float(sl_distance),
                'sl_percent': float(sl_percent),
                'swing_point': float(swing_point),
                'lookback': lookback,
                'buffer_percent': float(buffer_percent * 100),
                'method': 'swing',
                'direction': direction,
            })

        except Exception as e:
            self.log_error(f"Error calculating swing SL: {str(e)}", exc=e)
            return self.error_result(str(e))

    def calculate_optimal(
        self,
        entry_price: Decimal,
        direction: str,
        atr: Decimal = None,
        support: Decimal = None,
        resistance: Decimal = None,
        ohlcv_data: List[Dict] = None,
    ) -> ServiceResult:
        """
        Calculate optimal stop loss using multiple methods.

        Considers all available data and returns the most
        appropriate stop loss.

        Args:
            entry_price: Entry price
            direction: 'buy' or 'sell'
            atr: ATR value (optional)
            support: Support level (optional)
            resistance: Resistance level (optional)
            ohlcv_data: OHLCV data (optional)

        Returns:
            ServiceResult with optimal stop loss
        """
        candidates = []

        # ATR-based
        if atr:
            result = self.calculate_atr_based(entry_price, atr, direction)
            if result.success:
                candidates.append({
                    'method': 'atr',
                    'stop_loss': result.data['stop_loss'],
                    'sl_percent': result.data['sl_percent'],
                })

        # S/R-based
        if (direction == 'buy' and support) or (direction == 'sell' and resistance):
            result = self.calculate_support_resistance_based(
                entry_price, direction, support, resistance
            )
            if result.success:
                candidates.append({
                    'method': 'support_resistance',
                    'stop_loss': result.data['stop_loss'],
                    'sl_percent': result.data['sl_percent'],
                })

        # Swing-based
        if ohlcv_data and len(ohlcv_data) >= 20:
            result = self.calculate_swing_based(
                entry_price, ohlcv_data, direction
            )
            if result.success:
                candidates.append({
                    'method': 'swing',
                    'stop_loss': result.data['stop_loss'],
                    'sl_percent': result.data['sl_percent'],
                })

        # Fallback to percentage
        if not candidates:
            result = self.calculate_percentage_based(entry_price, direction)
            if result.success:
                candidates.append({
                    'method': 'percentage',
                    'stop_loss': result.data['stop_loss'],
                    'sl_percent': result.data['sl_percent'],
                })

        if not candidates:
            return self.error_result("Could not calculate any stop loss")

        # Select the tightest stop loss that's reasonable
        # (not too tight to get stopped out on noise)
        optimal = min(
            candidates,
            key=lambda x: x['sl_percent'] if x['sl_percent'] > 0.5 else float('inf')
        )

        return self.success_result({
            'stop_loss': optimal['stop_loss'],
            'sl_percent': optimal['sl_percent'],
            'method_used': optimal['method'],
            'all_candidates': candidates,
            'entry_price': float(entry_price),
            'direction': direction,
        })
