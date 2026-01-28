"""
Market Data Celery Tasks - Async data fetching tasks.

Provides Celery tasks for:
- Periodic data fetching
- Correlation calculation
- Data cleanup
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger('trading_bot')


@shared_task(bind=True, max_retries=3)
def fetch_all_pairs_data(self):
    """
    Fetch OHLCV data for all active trading pairs.

    This task runs every 5 minutes to keep data up-to-date.
    """
    from .services import DataFetcher
    from .models import TradingPair

    try:
        logger.info("Starting data fetch for all pairs")

        fetcher = DataFetcher()
        result = fetcher.fetch_all_pairs(timeframe='1h', limit=10)

        if result.success:
            logger.info(
                f"Data fetch completed: "
                f"{len(result.data['success'])} success, "
                f"{len(result.data['failed'])} failed"
            )
        else:
            logger.error(f"Data fetch failed: {result.error}")

        return result.data if result.success else {'error': result.error}

    except Exception as e:
        logger.error(f"Data fetch task failed: {str(e)}")
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True)
def fetch_pair_data(self, trading_pair_id: str, timeframe: str = '1h', limit: int = 100):
    """
    Fetch OHLCV data for a specific trading pair.

    Args:
        trading_pair_id: UUID of the trading pair
        timeframe: Candle timeframe
        limit: Number of candles to fetch
    """
    from .services import DataFetcher
    from .models import TradingPair

    try:
        pair = TradingPair.objects.get(id=trading_pair_id, is_active=True)
        fetcher = DataFetcher()

        result = fetcher.fetch_ohlcv(
            trading_pair=pair,
            timeframe=timeframe,
            limit=limit
        )

        return {
            'success': result.success,
            'data': result.data if result.success else None,
            'error': result.error if not result.success else None
        }

    except TradingPair.DoesNotExist:
        logger.error(f"Trading pair not found: {trading_pair_id}")
        return {'success': False, 'error': 'Trading pair not found'}
    except Exception as e:
        logger.error(f"Fetch pair data failed: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def calculate_correlations(timeframe: str = '1h', lookback_periods: int = 50):
    """
    Calculate correlation matrix for all trading pairs.

    Runs daily to update pair correlations for multi-pair validation.
    """
    from .models import TradingPair, OHLCV, CorrelationMatrix
    from django.db.models import Q
    import numpy as np
    from decimal import Decimal
    from datetime import date

    logger.info("Starting correlation calculation")

    pairs = list(TradingPair.objects.filter(is_active=True))
    today = date.today()
    created_count = 0

    for i, pair1 in enumerate(pairs):
        for pair2 in pairs[i + 1:]:
            try:
                # Get close prices for both pairs
                prices1 = list(OHLCV.objects.filter(
                    trading_pair=pair1,
                    timeframe=timeframe
                ).order_by('-timestamp')[:lookback_periods].values_list('close', flat=True))

                prices2 = list(OHLCV.objects.filter(
                    trading_pair=pair2,
                    timeframe=timeframe
                ).order_by('-timestamp')[:lookback_periods].values_list('close', flat=True))

                if len(prices1) < lookback_periods or len(prices2) < lookback_periods:
                    continue

                # Calculate correlation
                correlation = np.corrcoef(
                    [float(p) for p in prices1],
                    [float(p) for p in prices2]
                )[0, 1]

                # Save or update
                CorrelationMatrix.objects.update_or_create(
                    primary_pair=pair1,
                    secondary_pair=pair2,
                    timeframe=timeframe,
                    calculation_date=today,
                    defaults={
                        'correlation_value': Decimal(str(round(correlation, 4))),
                        'lookback_periods': lookback_periods,
                    }
                )
                created_count += 1

            except Exception as e:
                logger.error(
                    f"Error calculating correlation for "
                    f"{pair1.symbol} - {pair2.symbol}: {str(e)}"
                )

    logger.info(f"Correlation calculation completed: {created_count} pairs")
    return {'correlations_calculated': created_count}


@shared_task
def cleanup_old_data(days_to_keep: int = 365):
    """
    Clean up OHLCV data older than specified days.

    Keeps data for backtesting while preventing database bloat.
    """
    from .models import OHLCV

    cutoff_date = timezone.now() - timedelta(days=days_to_keep)

    deleted_count, _ = OHLCV.objects.filter(
        timestamp__lt=cutoff_date
    ).delete()

    logger.info(f"Cleaned up {deleted_count} old OHLCV records")
    return {'deleted_count': deleted_count}
