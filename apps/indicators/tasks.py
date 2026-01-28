"""
Indicators Celery Tasks - Async indicator calculations.
"""

from celery import shared_task
import logging

logger = logging.getLogger('trading_bot')


@shared_task
def calculate_all_indicators():
    """
    Calculate indicators for all active trading pairs.

    Runs every 5 minutes to keep indicator data up-to-date.
    """
    from apps.market_data.models import TradingPair, OHLCV
    from .services import IndicatorEngine

    logger.info("Starting indicator calculation for all pairs")

    pairs = TradingPair.objects.filter(is_active=True)
    engine = IndicatorEngine()
    results = {'success': 0, 'failed': 0}

    for pair in pairs:
        for timeframe in ['1h', '4h']:
            try:
                ohlcv_qs = OHLCV.objects.filter(
                    trading_pair=pair,
                    timeframe=timeframe
                ).order_by('-timestamp')[:100]

                ohlcv_data = [
                    {
                        'timestamp': o.timestamp,
                        'open': float(o.open),
                        'high': float(o.high),
                        'low': float(o.low),
                        'close': float(o.close),
                        'volume': float(o.volume),
                    }
                    for o in reversed(list(ohlcv_qs))
                ]

                if ohlcv_data:
                    engine.calculate_all(ohlcv_data)
                    results['success'] += 1

            except Exception as e:
                logger.error(f"Error calculating indicators for {pair.symbol} {timeframe}: {e}")
                results['failed'] += 1

    logger.info(f"Indicator calculation completed: {results}")
    return results
