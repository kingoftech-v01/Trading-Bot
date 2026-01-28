"""Celery tasks for the orders app."""

from celery import shared_task
import logging

logger = logging.getLogger('trading_bot')


@shared_task
def check_stop_loss_take_profit_task():
    """Check all positions for SL/TP triggers."""
    from .models import Position
    from .services import PositionManager, OrderExecutor

    positions = Position.objects.filter(is_active=True).select_related('trading_pair')
    manager = PositionManager()
    executor = OrderExecutor()

    triggered = 0
    for position in positions:
        current_price = position.current_price
        if not current_price:
            continue

        result = manager.check_stop_loss_take_profit(position, current_price)
        if result.success and result.data['triggers']:
            for trigger_type, trigger_price in result.data['triggers']:
                logger.info(f"Position {position.id} hit {trigger_type} at {trigger_price}")
                triggered += 1

    return {'checked': len(positions), 'triggered': triggered}


@shared_task
def update_position_prices_task():
    """Update all position prices and unrealized P&L."""
    from .models import Position
    from apps.market_data.models import OHLCV

    positions = Position.objects.filter(is_active=True).select_related('trading_pair')
    updated = 0

    for position in positions:
        latest = OHLCV.objects.filter(
            trading_pair=position.trading_pair
        ).order_by('-timestamp').first()

        if latest:
            position.update_pnl(latest.close)
            updated += 1

    return {'updated': updated}
