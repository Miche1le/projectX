from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Optional

from .repository import record_completed_message


class TelegramPublisher:
    def __init__(self, token: Optional[str], chat_id: Optional[str]) -> None:
        self.token = token
        self.chat_id = chat_id

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def send(self, task_id: str, telegram_id: str, short_summary: str, summary: str) -> None:
        delivered_at = None
        if self.token and self.chat_id:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": f"{short_summary}\n\n{summary}",
                "parse_mode": "HTML",
            }
            data = urllib.parse.urlencode(payload).encode("utf-8")
            request = urllib.request.Request(url, data=data)
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    body = response.read()
                    try:
                        result = json.loads(body)
                        if result.get("ok"):
                            delivered_at = self._now()
                    except json.JSONDecodeError:
                        delivered_at = self._now()
            except Exception:
                delivered_at = None
        else:
            print(f"[telegram] Task {task_id}: {short_summary}\n{summary}")  # noqa: T201
            delivered_at = self._now()

        if delivered_at:
            record_completed_message(task_id, telegram_id, short_summary, summary, delivered_at)
