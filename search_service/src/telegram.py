from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Optional

from .repository import record_completed_message

import logging

logger = logging.getLogger(__name__)


class TelegramPublisher:
    """
    Publisher that sends completed search results to a Telegram chat.

    If a token or chat_id is missing, messages are printed to stdout. When both are provided,
    the publisher attempts to send the message via Telegram, retrying on transient errors.
    The number of retry attempts and delay between retries can be configured via
    environment variables ``TELEGRAM_MAX_RETRIES`` and ``TELEGRAM_RETRY_DELAY`` (seconds).
    """

    def __init__(self, token: Optional[str], chat_id: Optional[str]) -> None:
        self.token = token
        self.chat_id = chat_id
        # Configure retry behaviour from environment
        try:
            self.max_retries = int(os.getenv("TELEGRAM_MAX_RETRIES", "3"))
        except ValueError:
            self.max_retries = 3
        try:
            self.retry_delay = float(os.getenv("TELEGRAM_RETRY_DELAY", "5"))
        except ValueError:
            self.retry_delay = 5.0

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def send(self, task_id: str, telegram_id: str, short_summary: str, summary: str) -> None:
        delivered_at: Optional[datetime] = None
        if self.token and self.chat_id:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": f"{short_summary}\n\n{summary}",
                "parse_mode": "HTML",
            }
            data = urllib.parse.urlencode(payload).encode("utf-8")
            request = urllib.request.Request(url, data=data)
            # Try to send message with retries on failure
            for attempt in range(1, self.max_retries + 1):
                try:
                    with urllib.request.urlopen(request, timeout=10) as response:
                        body = response.read()
                        try:
                            result = json.loads(body)
                            if result.get("ok"):
                                delivered_at = self._now()
                                break
                        except json.JSONDecodeError:
                            delivered_at = self._now()
                            break
                    # If API returned a non-OK response, raise to retry
                    logger.warning("Telegram API responded without OK flag on attempt %d", attempt)
                except Exception as exc:
                    logger.warning("Failed to send Telegram message on attempt %d: %s", attempt, exc)
                # Sleep before next retry if not last attempt
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
        else:
            # Fall back to console output if no token/chat is configured
            logger.info("[telegram] Task %s: %s\n%s", task_id, short_summary, summary)
            delivered_at = self._now()

        # Persist the delivery result if the message was delivered successfully
        if delivered_at:
            record_completed_message(task_id, telegram_id, short_summary, summary, delivered_at)
