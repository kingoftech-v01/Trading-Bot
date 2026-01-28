"""
Backtester - Main backtesting engine.
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
import logging

from apps.core.services.base_service import BaseService, ServiceResult
from apps.signals.services import SignalGenerator
from apps.market_data.models import OHLCV
from ..models import BacktestRun, BacktestTrade, BacktestResult
from .performance_metrics import PerformanceMetrics


logger = logging.getLogger('trading_bot')


class Backtester(BaseService):
    """
    Main backtesting engine.

    Simulates trading using historical data and the "5 out of 8" voting system.
    """

    def __init__(
        self,
        initial_balance: Decimal = Decimal('10000'),
        risk_per_trade: Decimal = Decimal('0.01'),
        voting_threshold: int = 5,
        min_confluence: float = 50.0,
    ):
        super().__init__()
        self.initial_balance = initial_balance
        self.risk_per_trade = risk_per_trade
        self.voting_threshold = voting_threshold
        self.min_confluence = min_confluence
        self.signal_generator = SignalGenerator(
            voting_threshold=voting_threshold,
            min_confluence=min_confluence,
        )
        self.metrics = PerformanceMetrics()

    def run_backtest(
        self,
        backtest_run: BacktestRun,
    ) -> ServiceResult:
        """
        Execute a backtest.

        Args:
            backtest_run: BacktestRun model instance

        Returns:
            ServiceResult with backtest results
        """
        try:
            # Update status
            backtest_run.status = 'running'
            backtest_run.started_at = timezone.now()
            backtest_run.save()

            # Get historical data
            ohlcv_data = self._get_historical_data(
                backtest_run.trading_pair,
                backtest_run.start_date,
                backtest_run.end_date,
                backtest_run.timeframe,
            )

            if len(ohlcv_data) < 200:
                return self.error_result("Not enough historical data")

            # Run simulation
            results = self._simulate_trading(backtest_run, ohlcv_data)

            # Calculate metrics
            metrics = self.metrics.calculate_all_metrics(
                results['trades'],
                results['equity_curve'],
                self.initial_balance,
            )

            # Update backtest run
            self._update_backtest_results(backtest_run, results, metrics)

            # Create detailed results
            self._create_detailed_results(backtest_run, results, metrics)

            backtest_run.status = 'completed'
            backtest_run.completed_at = timezone.now()
            backtest_run.save()

            self.log_info(
                f"Backtest completed: {backtest_run.name}, "
                f"{backtest_run.total_trades} trades, "
                f"{backtest_run.win_rate}% win rate"
            )

            return self.success_result({
                'backtest_id': str(backtest_run.id),
                'total_trades': backtest_run.total_trades,
                'win_rate': float(backtest_run.win_rate or 0),
                'total_return': float(backtest_run.total_return or 0),
                'sharpe_ratio': float(backtest_run.sharpe_ratio or 0),
            })

        except Exception as e:
            backtest_run.status = 'failed'
            backtest_run.error_message = str(e)
            backtest_run.save()
            self.log_error(f"Backtest failed: {str(e)}", exc=e)
            return self.error_result(str(e))

    def _get_historical_data(
        self,
        trading_pair,
        start_date,
        end_date,
        timeframe: str,
    ) -> List[Dict]:
        """Get historical OHLCV data."""
        ohlcv_qs = OHLCV.objects.filter(
            trading_pair=trading_pair,
            timeframe=timeframe,
            timestamp__gte=start_date,
            timestamp__lte=end_date,
        ).order_by('timestamp')

        return list(ohlcv_qs.values(
            'timestamp', 'open', 'high', 'low', 'close', 'volume'
        ))

    def _simulate_trading(
        self,
        backtest_run: BacktestRun,
        ohlcv_data: List[Dict],
    ) -> Dict[str, Any]:
        """Simulate trading on historical data."""
        balance = float(self.initial_balance)
        trades = []
        equity_curve = []
        current_position = None

        # Sliding window for signal generation
        window_size = 200

        for i in range(window_size, len(ohlcv_data)):
            window = ohlcv_data[i - window_size:i]
            current_bar = ohlcv_data[i]
            current_price = float(current_bar['close'])
            current_time = current_bar['timestamp']

            # Record equity
            equity_curve.append({
                'timestamp': current_time,
                'equity': balance,
            })

            # Check for position exit
            if current_position:
                exit_reason = self._check_exit_conditions(
                    current_position, current_bar
                )
                if exit_reason:
                    trade_result = self._close_position(
                        current_position,
                        current_price,
                        current_time,
                        exit_reason,
                    )
                    balance += trade_result['pnl']
                    trades.append(trade_result)

                    # Save trade
                    BacktestTrade.objects.create(
                        backtest_run=backtest_run,
                        signal_type=current_position['side'],
                        entry_time=current_position['entry_time'],
                        exit_time=current_time,
                        entry_price=Decimal(str(current_position['entry_price'])),
                        exit_price=Decimal(str(current_price)),
                        quantity=Decimal(str(current_position['quantity'])),
                        stop_loss=Decimal(str(current_position['stop_loss'])) if current_position.get('stop_loss') else None,
                        take_profit=Decimal(str(current_position['take_profit'])) if current_position.get('take_profit') else None,
                        pnl=Decimal(str(trade_result['pnl'])),
                        pnl_percent=Decimal(str(trade_result['pnl_percent'])),
                        exit_reason=exit_reason,
                        vote_count=current_position.get('vote_count', 0),
                        confluence_score=Decimal(str(current_position.get('confluence_score', 0))),
                    )

                    current_position = None
                continue

            # Generate signal if no position
            if not current_position:
                result = self.signal_generator.generate_signal(
                    trading_pair=backtest_run.trading_pair,
                    ohlcv_data=window,
                    timeframe=backtest_run.timeframe,
                    save_to_db=False,
                )

                if result.success and result.data.get('signal_generated'):
                    signal_data = result.data

                    # Calculate position size
                    risk_amount = balance * float(self.risk_per_trade)
                    sl_distance = abs(current_price - signal_data['stop_loss'])
                    if sl_distance > 0:
                        quantity = risk_amount / sl_distance
                    else:
                        continue

                    current_position = {
                        'side': signal_data['signal'],
                        'entry_price': current_price,
                        'entry_time': current_time,
                        'quantity': quantity,
                        'stop_loss': signal_data['stop_loss'],
                        'take_profit': signal_data['take_profit'],
                        'vote_count': signal_data['vote_count'],
                        'confluence_score': signal_data['confluence_score'],
                    }

        return {
            'trades': trades,
            'equity_curve': equity_curve,
            'final_balance': balance,
        }

    def _check_exit_conditions(
        self,
        position: Dict,
        current_bar: Dict,
    ) -> Optional[str]:
        """Check if position should be closed."""
        high = float(current_bar['high'])
        low = float(current_bar['low'])

        if position['side'] == 'buy':
            if position.get('stop_loss') and low <= position['stop_loss']:
                return 'stop_loss'
            if position.get('take_profit') and high >= position['take_profit']:
                return 'take_profit'
        else:  # sell
            if position.get('stop_loss') and high >= position['stop_loss']:
                return 'stop_loss'
            if position.get('take_profit') and low <= position['take_profit']:
                return 'take_profit'

        return None

    def _close_position(
        self,
        position: Dict,
        exit_price: float,
        exit_time,
        exit_reason: str,
    ) -> Dict:
        """Close a position and calculate P&L."""
        if position['side'] == 'buy':
            pnl = (exit_price - position['entry_price']) * position['quantity']
        else:
            pnl = (position['entry_price'] - exit_price) * position['quantity']

        entry_value = position['entry_price'] * position['quantity']
        pnl_percent = (pnl / entry_value) * 100 if entry_value > 0 else 0

        return {
            'side': position['side'],
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'quantity': position['quantity'],
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'exit_reason': exit_reason,
            'entry_time': position['entry_time'],
            'exit_time': exit_time,
        }

    def _update_backtest_results(
        self,
        backtest_run: BacktestRun,
        results: Dict,
        metrics: Dict,
    ):
        """Update backtest run with results."""
        trades = results['trades']
        winning = [t for t in trades if t['pnl'] > 0]
        losing = [t for t in trades if t['pnl'] < 0]

        backtest_run.total_trades = len(trades)
        backtest_run.winning_trades = len(winning)
        backtest_run.losing_trades = len(losing)
        backtest_run.final_balance = Decimal(str(results['final_balance']))

        if self.initial_balance > 0:
            backtest_run.total_return = Decimal(str(
                (results['final_balance'] - float(self.initial_balance)) / float(self.initial_balance) * 100
            ))

        if len(trades) > 0:
            backtest_run.win_rate = Decimal(str(len(winning) / len(trades) * 100))

        backtest_run.profit_factor = Decimal(str(metrics.get('profit_factor', 0)))
        backtest_run.max_drawdown = Decimal(str(metrics.get('max_drawdown', 0)))
        backtest_run.sharpe_ratio = Decimal(str(metrics.get('sharpe_ratio', 0)))

    def _create_detailed_results(
        self,
        backtest_run: BacktestRun,
        results: Dict,
        metrics: Dict,
    ):
        """Create detailed results record."""
        BacktestResult.objects.create(
            backtest_run=backtest_run,
            total_return_pct=Decimal(str(metrics.get('total_return_pct', 0))),
            max_drawdown_pct=Decimal(str(metrics.get('max_drawdown', 0))),
            sharpe_ratio=Decimal(str(metrics.get('sharpe_ratio', 0))),
            sortino_ratio=Decimal(str(metrics.get('sortino_ratio', 0))),
            avg_win=Decimal(str(metrics.get('avg_win', 0))),
            avg_loss=Decimal(str(metrics.get('avg_loss', 0))),
            largest_win=Decimal(str(metrics.get('largest_win', 0))),
            largest_loss=Decimal(str(metrics.get('largest_loss', 0))),
            equity_curve=results['equity_curve'],
        )
