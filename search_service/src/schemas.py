from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .statuses import SearchTaskStatus


def to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class SearchTaskCreateRequest(CamelModel):
    telegram_id: str = Field(..., description="Target Telegram chat identifier")
    text: str = Field(..., description="User query to run via AI search")


class SearchTaskCreateResponse(CamelModel):
    task_id: str = Field(..., description="Generated task identifier")
    status: SearchTaskStatus
    queued_at: datetime = Field(..., description="Timestamp when the task was queued")


class SearchTaskRetryResponse(CamelModel):
    task_id: str
    status: SearchTaskStatus


class SearchTaskView(CamelModel):
    task_id: str
    telegram_id: str
    text: str
    status: SearchTaskStatus
    short_summary: Optional[str] = None
    summary: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PaginationMeta(CamelModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class SearchTaskPage(CamelModel):
    data: List[SearchTaskView]
    meta: PaginationMeta


class RawSearchTaskMessage(CamelModel):
    task_id: str
    telegram_id: str
    text: str
    requested_at: datetime


class CompletedSearchTaskMessage(CamelModel):
    task_id: str
    telegram_id: str
    status: SearchTaskStatus
    short_summary: str
    summary: str
    completed_at: datetime
