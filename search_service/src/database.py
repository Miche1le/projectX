from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from .config import settings


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS search_tasks (
                id TEXT PRIMARY KEY,
                telegram_id TEXT NOT NULL,
                text TEXT NOT NULL,
                status TEXT NOT NULL,
                short_summary TEXT,
                summary TEXT,
                error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS completed_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                telegram_id TEXT NOT NULL,
                short_summary TEXT NOT NULL,
                summary TEXT NOT NULL,
                delivered_at TEXT,
                FOREIGN KEY(task_id) REFERENCES search_tasks(id)
            )
            """
        )
        conn.commit()
