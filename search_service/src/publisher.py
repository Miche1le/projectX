from __future__ import annotations

from .database import init_db
from .queueing import consume_completed_tasks
from .schemas import CompletedSearchTaskMessage
from .telegram import TelegramPublisher
from .config import settings


publisher = TelegramPublisher(settings.telegram_bot_token, settings.telegram_chat_id)


def _handle(message: CompletedSearchTaskMessage) -> None:
    publisher.send(
        task_id=message.task_id,
        telegram_id=message.telegram_id,
        short_summary=message.short_summary,
        summary=message.summary,
    )


def main() -> None:
    init_db()
    consume_completed_tasks(_handle)


if __name__ == "__main__":
    main()
