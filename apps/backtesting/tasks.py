"""Celery tasks for the backtesting app."""

from celery import shared_task
import logging

logger = logging.getLogger('trading_bot')


@shared_task(bind=True, max_retries=3)
def run_backtest_task(self, backtest_id: str):
    """Run a backtest asynchronously."""
    from .models import BacktestRun
    from .services import Backtester

    try:
        backtest = BacktestRun.objects.get(id=backtest_id)
    except BacktestRun.DoesNotExist:
        logger.error(f"Backtest not found: {backtest_id}")
        return {'error': 'Backtest not found'}

    backtester = Backtester(
        initial_balance=backtest.initial_balance,
        risk_per_trade=backtest.risk_per_trade,
        voting_threshold=backtest.voting_threshold,
        min_confluence=float(backtest.min_confluence),
    )

    result = backtester.run_backtest(backtest)

    if result.success:
        return result.data
    return {'error': result.error}
