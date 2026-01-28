"""
Celery tasks for the signals app.

Async tasks for signal generation and management.
"""

from celery import shared_task
from django.utils import timezone
import logging

from apps.market_data.models import TradingPair, OHLCV


logger = logging.getLogger('trading_bot')


@shared_task(bind=True, max_retries=3)
def generate_signal_task(
    self,
    trading_pair_id: str,
    timeframe: str = '1h',
    min_confluence: float = 50.0,
    min_confidence: float = 60.0,
):
    """
    Generate a signal for a trading pair.

    Args:
        trading_pair_id: UUID of the trading pair
        timeframe: Timeframe for analysis
        min_confluence: Minimum confluence score
        min_confidence: Minimum confidence

    Returns:
        dict: Signal generation result
    """
    from .services import SignalGenerator

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

    # Generate signal
    generator = SignalGenerator(
        min_confluence=min_confluence,
        min_confidence=min_confidence,
    )
    result = generator.generate_signal(
        trading_pair=trading_pair,
        ohlcv_data=ohlcv_data,
        timeframe=timeframe,
    )

    if result.success:
        logger.info(
            f"Signal task completed for {trading_pair.symbol}: "
            f"{result.data.get('signal', 'wait')}"
        )
        return result.data
    else:
        logger.error(f"Signal generation failed: {result.error}")
        return {'error': result.error}


@shared_task
def generate_signals_for_all_pairs_task(
    timeframe: str = '1h',
    min_confluence: float = 50.0,
    min_confidence: float = 60.0,
):
    """
    Generate signals for all active trading pairs.

    Args:
        timeframe: Timeframe for analysis
        min_confluence: Minimum confluence score
        min_confidence: Minimum confidence

    Returns:
        dict: Summary of signal generation
    """
    trading_pairs = TradingPair.objects.filter(is_active=True)
    results = {
        'total_pairs': trading_pairs.count(),
        'signals_generated': 0,
        'no_signal': 0,
        'errors': 0,
    }

    for pair in trading_pairs:
        try:
            generate_signal_task.delay(
                str(pair.id),
                timeframe,
                min_confluence,
                min_confidence,
            )
            results['signals_generated'] += 1
        except Exception as e:
            logger.error(f"Error queuing signal for {pair.symbol}: {str(e)}")
            results['errors'] += 1

    logger.info(
        f"Queued {results['signals_generated']} signal generation tasks"
    )

    return results


@shared_task
def expire_old_signals_task():
    """
    Mark expired signals as expired.

    Returns:
        dict: Number of signals expired
    """
    from .models import Signal

    expired_count = Signal.objects.filter(
        status='pending',
        expires_at__lt=timezone.now(),
    ).update(status='expired')

    if expired_count:
        logger.info(f"Expired {expired_count} old signals")

    return {'expired_count': expired_count}


@shared_task
def cleanup_old_sessions_task(days: int = 30):
    """
    Delete old signal sessions and related data.

    Args:
        days: Number of days to keep

    Returns:
        dict: Cleanup summary
    """
    from .models import SignalSession, Vote, ConfluenceScore

    cutoff = timezone.now() - timezone.timedelta(days=days)

    # Delete old sessions (cascades to votes and confluence scores)
    deleted_sessions, _ = SignalSession.objects.filter(
        evaluated_at__lt=cutoff
    ).delete()

    logger.info(f"Deleted {deleted_sessions} old signal sessions")

    return {
        'deleted_sessions': deleted_sessions,
        'cutoff_date': cutoff.isoformat(),
    }


@shared_task(bind=True, max_retries=3)
def validate_signal_with_correlations_task(
    self,
    signal_id: str,
):
    """
    Validate a signal using correlated pairs.

    Args:
        signal_id: UUID of the signal to validate

    Returns:
        dict: Validation result
    """
    from .models import Signal
    from .services import MultiPairValidator

    try:
        signal = Signal.objects.get(id=signal_id)
    except Signal.DoesNotExist:
        logger.error(f"Signal not found: {signal_id}")
        return {'error': 'Signal not found'}

    validator = MultiPairValidator()
    result = validator.validate_with_correlations(
        primary_pair=signal.trading_pair,
        primary_signal=signal.signal,
        timeframe=signal.timeframe,
    )

    if result.success:
        # Update signal metadata with validation result
        signal.metadata['correlation_validation'] = result.data
        signal.save(update_fields=['metadata'])
        logger.info(
            f"Signal {signal_id} validated: "
            f"{result.data['confirmations']} confirmations"
        )

    return result.data if result.success else {'error': result.error}


@shared_task(bind=True, max_retries=3)
def send_signal_notification_task(self, signal_id: str):
    """
    Send notification for a new signal.

    Sends notifications through all configured channels:
    - Logging (always enabled)
    - Email (if configured via TRADING_NOTIFICATION_EMAIL)
    - Webhook (if configured via TRADING_NOTIFICATION_WEBHOOK_URL)

    Args:
        signal_id: UUID of the signal

    Returns:
        dict: Notification result with channel statuses
    """
    from .models import Signal
    from .services import NotificationService, NotificationPayload

    try:
        signal = Signal.objects.select_related('trading_pair').get(id=signal_id)
    except Signal.DoesNotExist:
        logger.error(f"Signal not found: {signal_id}")
        return {'error': 'Signal not found'}

    # Create notification payload
    payload = NotificationPayload(
        signal_id=str(signal.id),
        trading_pair=signal.trading_pair.symbol,
        signal_type=signal.signal,
        confluence_score=float(signal.confluence_score),
        vote_count=signal.vote_count,
        entry_price=str(signal.entry_price),
        stop_loss=str(signal.stop_loss),
        take_profit=str(signal.take_profit),
        timeframe=signal.timeframe,
        metadata={
            'created_at': signal.created_at.isoformat() if signal.created_at else None,
            'expires_at': signal.expires_at.isoformat() if signal.expires_at else None,
        },
    )

    # Send notification through all configured channels
    notification_service = NotificationService()
    result = notification_service.send_signal_notification(payload)

    if result.success:
        logger.info(
            f"Signal notification sent for {signal.trading_pair.symbol}: "
            f"channels={result.data['channels_succeeded']}"
        )
    else:
        logger.error(
            f"Signal notification failed for {signal.trading_pair.symbol}: "
            f"{result.error}"
        )
        # Retry on failure
        try:
            self.retry(countdown=60)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for signal notification: {signal_id}")

    return {
        'sent': result.success,
        'signal_id': str(signal.id),
        'trading_pair': signal.trading_pair.symbol,
        'channels_attempted': result.data.get('channels_attempted', []),
        'channels_succeeded': result.data.get('channels_succeeded', []),
        'channels_failed': result.data.get('channels_failed', []),
        'errors': result.data.get('errors', []),
    }
