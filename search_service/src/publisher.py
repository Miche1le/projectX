from __future__ import annotations

from .database import init_db
from .queueing import consume_completed_tasks
from .schemas import CompletedSearchTaskMessage
from .telegram import TelegramPublisher
from .config import settings

import logging

logger = logging.getLogger(__name__)

# Instantiate the publisher using configuration. It will either send to Telegram or log to console.
publisher = TelegramPublisher(settings.telegram_bot_token, settings.telegram_chat_id)


def _handle(message: CompletedSearchTaskMessage) -> None:
    """
    Handle a completed search task by sending it to Telegram.

    Exceptions during sending are logged; the caller will mark the message as acknowledged.
    """
    try:
        publisher.send(
            task_id=message.task_id,
            telegram_id=message.telegram_id,
            short_summary=message.short_summary,
            summary=message.summary,
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.exception("Failed to publish completed task %s: %s", message.task_id, exc)


def main() -> None:
    init_db()
    consume_completed_tasks(_handle)


if __name__ == "__main__":
    main()
