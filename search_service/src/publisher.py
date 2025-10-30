from __future__ import annotations

import logging

from .config import settings
from .database import init_db
from .queueing import consume_completed_tasks
from .schemas import CompletedSearchTaskMessage
from .telegram import TelegramPublisher

logger = logging.getLogger(__name__)

publisher = TelegramPublisher(settings.telegram_bot_token, settings.telegram_chat_id)


def _handle(message: CompletedSearchTaskMessage) -> None:
    try:
        publisher.send(
            task_id=message.task_id,
            telegram_id=message.telegram_id,
            short_summary=message.short_summary,
            summary=message.summary,
        )
    except Exception as exc:
        logger.exception("Failed to publish completed task %s: %s", message.task_id, exc)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    init_db()
    consume_completed_tasks(_handle)


if __name__ == "__main__":
    main()
