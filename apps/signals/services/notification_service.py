"""
Notification Service for trading signals.

Handles sending notifications through various channels:
- Logging (always enabled)
- Email (optional)
- Webhooks (optional)

Future integrations:
- Telegram
- Discord
- Slack
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
import requests

from apps.core.services.base_service import BaseService, ServiceResult


logger = logging.getLogger('trading_bot.notifications')


class NotificationChannel(Enum):
    """Available notification channels."""
    LOG = 'log'
    EMAIL = 'email'
    WEBHOOK = 'webhook'


@dataclass
class NotificationPayload:
    """Data structure for notification payload."""
    signal_id: str
    trading_pair: str
    signal_type: str  # 'buy' or 'sell'
    confluence_score: float
    vote_count: int
    entry_price: str
    stop_loss: str
    take_profit: str
    timeframe: str
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert payload to dictionary."""
        return {
            'signal_id': self.signal_id,
            'trading_pair': self.trading_pair,
            'signal_type': self.signal_type,
            'confluence_score': self.confluence_score,
            'vote_count': self.vote_count,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'timeframe': self.timeframe,
            'metadata': self.metadata or {},
        }

    def format_message(self) -> str:
        """Format payload as human-readable message."""
        signal_emoji = '🟢' if self.signal_type == 'buy' else '🔴'
        return (
            f"{signal_emoji} {self.signal_type.upper()} Signal: {self.trading_pair}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Confluence Score: {self.confluence_score:.1f}%\n"
            f"Votes: {self.vote_count}/8\n"
            f"Timeframe: {self.timeframe}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Entry: {self.entry_price}\n"
            f"Stop Loss: {self.stop_loss}\n"
            f"Take Profit: {self.take_profit}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Signal ID: {self.signal_id}"
        )


class NotificationService(BaseService):
    """
    Service for sending signal notifications.

    Supports multiple channels and can be configured via Django settings.
    """

    def __init__(self):
        """Initialize notification service with configured channels."""
        self.enabled_channels: List[NotificationChannel] = [NotificationChannel.LOG]

        # Check for email configuration
        if self._is_email_configured():
            self.enabled_channels.append(NotificationChannel.EMAIL)

        # Check for webhook configuration
        if self._is_webhook_configured():
            self.enabled_channels.append(NotificationChannel.WEBHOOK)

    def _is_email_configured(self) -> bool:
        """Check if email is configured."""
        return all([
            getattr(settings, 'EMAIL_HOST', None),
            getattr(settings, 'TRADING_NOTIFICATION_EMAIL', None),
        ])

    def _is_webhook_configured(self) -> bool:
        """Check if webhook is configured."""
        return bool(getattr(settings, 'TRADING_NOTIFICATION_WEBHOOK_URL', None))

    def send_signal_notification(
        self,
        payload: NotificationPayload,
        channels: Optional[List[NotificationChannel]] = None,
    ) -> ServiceResult:
        """
        Send notification for a new trading signal.

        Args:
            payload: Notification payload with signal data
            channels: Specific channels to use (defaults to all enabled)

        Returns:
            ServiceResult with notification status
        """
        channels_to_use = channels or self.enabled_channels
        results = {
            'channels_attempted': [],
            'channels_succeeded': [],
            'channels_failed': [],
            'errors': [],
        }

        for channel in channels_to_use:
            try:
                results['channels_attempted'].append(channel.value)

                if channel == NotificationChannel.LOG:
                    self._send_log_notification(payload)
                elif channel == NotificationChannel.EMAIL:
                    self._send_email_notification(payload)
                elif channel == NotificationChannel.WEBHOOK:
                    self._send_webhook_notification(payload)

                results['channels_succeeded'].append(channel.value)

            except Exception as e:
                results['channels_failed'].append(channel.value)
                results['errors'].append({
                    'channel': channel.value,
                    'error': str(e),
                })
                logger.error(f"Failed to send {channel.value} notification: {e}")

        # Consider success if at least one channel succeeded
        success = len(results['channels_succeeded']) > 0

        return ServiceResult(
            success=success,
            data=results,
            error=None if success else 'All notification channels failed',
        )

    def _send_log_notification(self, payload: NotificationPayload) -> None:
        """Send notification to log."""
        message = payload.format_message()
        logger.info(f"TRADING SIGNAL NOTIFICATION:\n{message}")

        # Also log structured data for monitoring tools
        logger.info(
            "Signal notification",
            extra={
                'signal_id': payload.signal_id,
                'trading_pair': payload.trading_pair,
                'signal_type': payload.signal_type,
                'confluence_score': payload.confluence_score,
                'vote_count': payload.vote_count,
            }
        )

    def _send_email_notification(self, payload: NotificationPayload) -> None:
        """Send notification via email."""
        recipient = getattr(settings, 'TRADING_NOTIFICATION_EMAIL', None)
        if not recipient:
            raise ValueError("TRADING_NOTIFICATION_EMAIL not configured")

        subject = f"Trading Signal: {payload.signal_type.upper()} {payload.trading_pair}"

        # Plain text message
        text_message = payload.format_message()

        # Try to render HTML template if available
        try:
            html_message = render_to_string(
                'signals/email/signal_notification.html',
                {'payload': payload, 'data': payload.to_dict()}
            )
        except Exception:
            html_message = None

        send_mail(
            subject=subject,
            message=text_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'trading-bot@localhost'),
            recipient_list=[recipient] if isinstance(recipient, str) else recipient,
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Email notification sent to {recipient}")

    def _send_webhook_notification(self, payload: NotificationPayload) -> None:
        """Send notification via webhook."""
        webhook_url = getattr(settings, 'TRADING_NOTIFICATION_WEBHOOK_URL', None)
        if not webhook_url:
            raise ValueError("TRADING_NOTIFICATION_WEBHOOK_URL not configured")

        webhook_secret = getattr(settings, 'TRADING_NOTIFICATION_WEBHOOK_SECRET', None)

        headers = {
            'Content-Type': 'application/json',
        }
        if webhook_secret:
            headers['X-Webhook-Secret'] = webhook_secret

        response = requests.post(
            webhook_url,
            json=payload.to_dict(),
            headers=headers,
            timeout=10,
        )

        response.raise_for_status()
        logger.info(f"Webhook notification sent to {webhook_url}")

    def test_channels(self) -> ServiceResult:
        """
        Test all configured notification channels.

        Returns:
            ServiceResult with test results for each channel
        """
        test_payload = NotificationPayload(
            signal_id='test-signal-id',
            trading_pair='TEST/USD',
            signal_type='buy',
            confluence_score=75.0,
            vote_count=6,
            entry_price='100.00',
            stop_loss='95.00',
            take_profit='115.00',
            timeframe='1h',
            metadata={'test': True},
        )

        return self.send_signal_notification(test_payload)
