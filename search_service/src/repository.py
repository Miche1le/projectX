from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Sequence
from uuid import uuid4

from .database import get_connection
from .statuses import SearchTaskStatus


@dataclass(slots=True)
class SearchTask:
    id: str
    telegram_id: str
    text: str
    status: SearchTaskStatus
    short_summary: str | None
    summary: str | None
    error: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: Any) -> "SearchTask":
        return cls(
            id=row["id"],
            telegram_id=row["telegram_id"],
            text=row["text"],
            status=SearchTaskStatus(row["status"]),
            short_summary=row["short_summary"],
            summary=row["summary"],
            error=row["error"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_task(telegram_id: str, text: str) -> SearchTask:
    task_id = str(uuid4())
    now = _utcnow()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO search_tasks (id, telegram_id, text, status, short_summary, summary, error, created_at, updated_at)
            VALUES (?, ?, ?, ?, NULL, NULL, NULL, ?, ?)
            """,
            (
                task_id,
                telegram_id,
                text,
                SearchTaskStatus.QUEUED.value,
                now.isoformat(),
                now.isoformat(),
            ),
        )
        conn.commit()

        row = conn.execute("SELECT * FROM search_tasks WHERE id = ?", (task_id,)).fetchone()

    return SearchTask.from_row(row)


def get_task(task_id: str) -> SearchTask | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM search_tasks WHERE id = ?", (task_id,)).fetchone()
    return SearchTask.from_row(row) if row else None


def list_tasks(status: SearchTaskStatus | None, page: int, page_size: int) -> tuple[list[SearchTask], dict[str, int]]:
    offset = (page - 1) * page_size
    params: list[Any] = []
    where_clause = ""
    if status:
        where_clause = "WHERE status = ?"
        params.append(status.value)

    query = f"""
        SELECT * FROM search_tasks
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])

    total_params: Sequence[Any] = ()
    if status:
        total_params = (status.value,)

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        total_query = "SELECT COUNT(1) FROM search_tasks"
        if status:
            total_query += " WHERE status = ?"
        total = conn.execute(total_query, total_params).fetchone()[0]

    tasks = [SearchTask.from_row(row) for row in rows]
    total_pages = (total + page_size - 1) // page_size if page_size else 1
    return tasks, {"page": page, "page_size": page_size, "total_items": total, "total_pages": total_pages}


def update_status(task_id: str, status: SearchTaskStatus) -> SearchTask | None:
    now = _utcnow()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE search_tasks
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (status.value, now.isoformat(), task_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM search_tasks WHERE id = ?", (task_id,)).fetchone()

    return SearchTask.from_row(row) if row else None


def save_result(task_id: str, short_summary: str, summary: str, status: SearchTaskStatus, error: str | None = None) -> SearchTask | None:
    now = _utcnow()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE search_tasks
            SET short_summary = ?, summary = ?, status = ?, error = ?, updated_at = ?
            WHERE id = ?
            """,
            (short_summary, summary, status.value, error, now.isoformat(), task_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM search_tasks WHERE id = ?", (task_id,)).fetchone()
    return SearchTask.from_row(row) if row else None


def reset_to_queue(task_id: str) -> SearchTask | None:
    now = _utcnow()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE search_tasks
            SET status = ?, short_summary = NULL, summary = NULL, error = NULL, updated_at = ?
            WHERE id = ?
            """,
            (SearchTaskStatus.QUEUED.value, now.isoformat(), task_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM search_tasks WHERE id = ?", (task_id,)).fetchone()
    return SearchTask.from_row(row) if row else None


def record_completed_message(task_id: str, telegram_id: str, short_summary: str, summary: str, delivered_at: datetime | None = None) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO completed_messages (task_id, telegram_id, short_summary, summary, delivered_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                task_id,
                telegram_id,
                short_summary,
                summary,
                delivered_at.isoformat() if delivered_at else None,
            ),
        )
        conn.commit()


def to_dict(task: SearchTask) -> dict[str, Any]:
    result = asdict(task)
    result["status"] = task.status.value
    result["created_at"] = task.created_at.isoformat()
    result["updated_at"] = task.updated_at.isoformat()
    return result
