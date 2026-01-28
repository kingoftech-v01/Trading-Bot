"""
Celery tasks for the combinations app.

Async tasks for evaluating combinations and processing results.
"""

from celery import shared_task
from django.utils import timezone
import logging

from .models import Combination, CombinationResult
from .services import CombinationEvaluator
from apps.market_data.models import TradingPair, OHLCV


logger = logging.getLogger('trading_bot')


@shared_task(bind=True, max_retries=3)
def evaluate_all_combinations_task(
    self,
    trading_pair_id: str,
    timeframe: str = '1h'
):
    """
    Evaluate all 8 combinations for a trading pair.

    Args:
        trading_pair_id: UUID of the trading pair
        timeframe: Timeframe for analysis

    Returns:
        dict: Evaluation results
    """
    try:
        trading_pair = TradingPair.objects.get(id=trading_pair_id)
    except TradingPair.DoesNotExist:
        logger.error(f"Trading pair not found: {trading_pair_id}")
        return {'error': 'Trading pair not found'}

    # Get OHLCV data
    ohlcv_qs = OHLCV.objects.filter(
        trading_pair=trading_pair,
        timeframe=timeframe
    ).order_by('-timestamp')[:200]

    if not ohlcv_qs.exists():
        logger.warning(f"No OHLCV data for {trading_pair.symbol} {timeframe}")
        return {'error': 'No OHLCV data available'}

    ohlcv_data = list(ohlcv_qs.values(
        'timestamp', 'open', 'high', 'low', 'close', 'volume'
    ))
    ohlcv_data.reverse()

    # Evaluate all combinations
    evaluator = CombinationEvaluator()
    results = evaluator.evaluate_all(ohlcv_data)

    # Save results to database
    saved_count = 0
    for combo_name, combo_result in results['details'].items():
        try:
            combination = Combination.objects.get(name=combo_name)
            CombinationResult.objects.create(
                combination=combination,
                trading_pair=trading_pair,
                timeframe=timeframe,
                signal=combo_result['signal'],
                confidence=combo_result['confidence'],
                criteria_met=combo_result['criteria_met'],
                criteria_details=combo_result.get('criteria_details', {}),
                indicator_values=combo_result.get('indicator_values', {}),
            )
            saved_count += 1
        except Combination.DoesNotExist:
            logger.warning(f"Combination not found in DB: {combo_name}")
        except Exception as e:
            logger.error(f"Error saving result for {combo_name}: {str(e)}")

    logger.info(
        f"Evaluated {len(results['details'])} combinations for "
        f"{trading_pair.symbol}, saved {saved_count} results"
    )

    return {
        'trading_pair': str(trading_pair_id),
        'timeframe': timeframe,
        'buy_votes': len(results['buy_votes']),
        'sell_votes': len(results['sell_votes']),
        'neutral_votes': len(results['neutral_votes']),
        'saved_count': saved_count,
    }


@shared_task(bind=True, max_retries=3)
def evaluate_single_combination_task(
    self,
    combination_name: str,
    trading_pair_id: str,
    timeframe: str = '1h'
):
    """
    Evaluate a single combination for a trading pair.

    Args:
        combination_name: Name of the combination
        trading_pair_id: UUID of the trading pair
        timeframe: Timeframe for analysis

    Returns:
        dict: Evaluation result
    """
    try:
        trading_pair = TradingPair.objects.get(id=trading_pair_id)
    except TradingPair.DoesNotExist:
        logger.error(f"Trading pair not found: {trading_pair_id}")
        return {'error': 'Trading pair not found'}

    # Get OHLCV data
    ohlcv_qs = OHLCV.objects.filter(
        trading_pair=trading_pair,
        timeframe=timeframe
    ).order_by('-timestamp')[:200]

    if not ohlcv_qs.exists():
        return {'error': 'No OHLCV data available'}

    ohlcv_data = list(ohlcv_qs.values(
        'timestamp', 'open', 'high', 'low', 'close', 'volume'
    ))
    ohlcv_data.reverse()

    # Evaluate
    evaluator = CombinationEvaluator()
    result = evaluator.evaluate_single(combination_name, ohlcv_data)

    if result is None:
        return {'error': f'Combination not found: {combination_name}'}

    # Save result
    try:
        combination = Combination.objects.get(name=combination_name)
        CombinationResult.objects.create(
            combination=combination,
            trading_pair=trading_pair,
            timeframe=timeframe,
            signal=result['signal'],
            confidence=result['confidence'],
            criteria_met=result['criteria_met'],
        )
    except Combination.DoesNotExist:
        pass

    return result


@shared_task
def evaluate_all_pairs_task(timeframe: str = '1h'):
    """
    Evaluate all active trading pairs with all combinations.

    Args:
        timeframe: Timeframe for analysis

    Returns:
        dict: Summary of evaluations
    """
    trading_pairs = TradingPair.objects.filter(is_active=True)
    results = {
        'total_pairs': trading_pairs.count(),
        'evaluated': 0,
        'errors': 0,
    }

    for pair in trading_pairs:
        try:
            evaluate_all_combinations_task.delay(str(pair.id), timeframe)
            results['evaluated'] += 1
        except Exception as e:
            logger.error(f"Error queuing evaluation for {pair.symbol}: {str(e)}")
            results['errors'] += 1

    logger.info(
        f"Queued {results['evaluated']} pairs for evaluation, "
        f"{results['errors']} errors"
    )

    return results


@shared_task
def cleanup_old_results_task(days: int = 30):
    """
    Delete combination results older than specified days.

    Args:
        days: Number of days to keep

    Returns:
        dict: Cleanup summary
    """
    cutoff = timezone.now() - timezone.timedelta(days=days)
    deleted_count, _ = CombinationResult.objects.filter(
        evaluated_at__lt=cutoff
    ).delete()

    logger.info(f"Deleted {deleted_count} old combination results")

    return {
        'deleted_count': deleted_count,
        'cutoff_date': cutoff.isoformat(),
    }
