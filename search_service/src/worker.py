from __future__ import annotations

from datetime import datetime, timezone

import logging

from .ai_search import run_ai_search
from .database import init_db
from .queueing import consume_raw_tasks
from .repository import save_result, update_status
from .schemas import CompletedSearchTaskMessage, RawSearchTaskMessage
from .statuses import SearchTaskStatus

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def handle(task: RawSearchTaskMessage) -> CompletedSearchTaskMessage:
    logger.info("Processing task %s", task.task_id)
    update_status(task.task_id, SearchTaskStatus.PROCESSING)
    short_summary, summary = run_ai_search(task.text)
    save_result(
        task_id=task.task_id,
        short_summary=short_summary,
        summary=summary,
        status=SearchTaskStatus.DONE,
    )
    completed_at = _utcnow()
    logger.info("Task %s processed successfully", task.task_id)
    return CompletedSearchTaskMessage(
        task_id=task.task_id,
        telegram_id=task.telegram_id,
        status=SearchTaskStatus.DONE,
        short_summary=short_summary,
        summary=summary,
        completed_at=completed_at,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    init_db()
    consume_raw_tasks(handle, prefetch_count=1)


if __name__ == "__main__":
    main()
