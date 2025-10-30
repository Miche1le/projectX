from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


@dataclass
class Settings:
    rabbitmq_url: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    db_path: Path = Path(os.getenv("SEARCH_DB_PATH", DATA_DIR / "search_tasks.db"))
    completed_queue_name: str = os.getenv("COMPLETED_QUEUE", "completed_search_tasks")
    raw_queue_name: str = os.getenv("RAW_QUEUE", "raw_search_tasks")
    telegram_bot_token: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str | None = os.getenv("TELEGRAM_CHAT_ID")


settings = Settings()
