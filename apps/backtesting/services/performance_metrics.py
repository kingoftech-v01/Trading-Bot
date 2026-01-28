"""
Performance Metrics - Calculate trading performance metrics.
"""

from typing import Dict, Any, List
from decimal import Decimal
import math
import logging

from apps.core.services.base_service import BaseService


logger = logging.getLogger('trading_bot')


class PerformanceMetrics(BaseService):
    """Calculates various performance metrics for backtesting."""

    def calculate_all_metrics(
        self,
        trades: List[Dict],
        equity_curve: List[Dict],
        initial_balance: Decimal,
    ) -> Dict[str, Any]:
        """Calculate all performance metrics."""
        if not trades:
            return self._empty_metrics()

        pnls = [t['pnl'] for t in trades]
        winning_pnls = [p for p in pnls if p > 0]
        losing_pnls = [p for p in pnls if p < 0]

        total_pnl = sum(pnls)
        gross_profit = sum(winning_pnls) if winning_pnls else 0
        gross_loss = abs(sum(losing_pnls)) if losing_pnls else 1

        return {
            'total_trades': len(trades),
            'winning_trades': len(winning_pnls),
            'losing_trades': len(losing_pnls),
            'win_rate': len(winning_pnls) / len(trades) * 100 if trades else 0,
            'total_pnl': total_pnl,
            'total_return_pct': total_pnl / float(initial_balance) * 100,
            'profit_factor': gross_profit / gross_loss if gross_loss > 0 else 0,
            'avg_win': sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0,
            'avg_loss': sum(losing_pnls) / len(losing_pnls) if losing_pnls else 0,
            'largest_win': max(winning_pnls) if winning_pnls else 0,
            'largest_loss': min(losing_pnls) if losing_pnls else 0,
            'max_drawdown': self._calculate_max_drawdown(equity_curve),
            'sharpe_ratio': self._calculate_sharpe_ratio(pnls),
            'sortino_ratio': self._calculate_sortino_ratio(pnls),
        }

    def _calculate_max_drawdown(self, equity_curve: List[Dict]) -> float:
        """Calculate maximum drawdown."""
        if not equity_curve:
            return 0

        equities = [e['equity'] for e in equity_curve]
        peak = equities[0]
        max_dd = 0

        for equity in equities:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak * 100
            if drawdown > max_dd:
                max_dd = drawdown

        return max_dd

    def _calculate_sharpe_ratio(
        self,
        returns: List[float],
        risk_free_rate: float = 0.02,
        periods_per_year: int = 252,
    ) -> float:
        """Calculate Sharpe ratio."""
        if len(returns) < 2:
            return 0

        avg_return = sum(returns) / len(returns)
        std_return = math.sqrt(sum((r - avg_return) ** 2 for r in returns) / len(returns))

        if std_return == 0:
            return 0

        sharpe = (avg_return - risk_free_rate / periods_per_year) / std_return
        return sharpe * math.sqrt(periods_per_year)

    def _calculate_sortino_ratio(
        self,
        returns: List[float],
        risk_free_rate: float = 0.02,
        periods_per_year: int = 252,
    ) -> float:
        """Calculate Sortino ratio (downside risk only)."""
        if len(returns) < 2:
            return 0

        avg_return = sum(returns) / len(returns)
        downside_returns = [r for r in returns if r < 0]

        if not downside_returns:
            return 0

        downside_std = math.sqrt(sum(r ** 2 for r in downside_returns) / len(downside_returns))

        if downside_std == 0:
            return 0

        sortino = (avg_return - risk_free_rate / periods_per_year) / downside_std
        return sortino * math.sqrt(periods_per_year)

    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure."""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'total_return_pct': 0,
            'profit_factor': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'largest_win': 0,
            'largest_loss': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
        }
