from __future__ import annotations

from enum import Enum


class SearchTaskStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"
