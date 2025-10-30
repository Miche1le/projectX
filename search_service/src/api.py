from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Query

from .database import init_db
from .queueing import publish_raw_task
from .repository import (
    create_task,
    get_task,
    list_tasks,
    reset_to_queue,
    to_dict,
)
from .schemas import (
    RawSearchTaskMessage,
    SearchTaskCreateRequest,
    SearchTaskCreateResponse,
    SearchTaskPage,
    SearchTaskRetryResponse,
    SearchTaskView,
)
from .statuses import SearchTaskStatus

app = FastAPI(title="Search Service", version="1.0.0")


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.post("/api/v1/search-tasks", response_model=SearchTaskCreateResponse, status_code=201)
async def enqueue_search_task(payload: SearchTaskCreateRequest) -> SearchTaskCreateResponse:
    task = create_task(telegram_id=payload.telegram_id, text=payload.text)
    message = RawSearchTaskMessage(
        task_id=task.id,
        telegram_id=task.telegram_id,
        text=task.text,
        requested_at=datetime.now(timezone.utc),
    )
    publish_raw_task(message)
    return SearchTaskCreateResponse(task_id=task.id, status=task.status, queued_at=task.created_at)


@app.get("/api/v1/search-tasks", response_model=SearchTaskPage)
async def search_tasks(
    status: Optional[SearchTaskStatus] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
) -> SearchTaskPage:
    tasks, meta = list_tasks(status=status, page=page, page_size=page_size)
    views = [
        SearchTaskView.model_validate(
            {
                "task_id": task.id,
                "telegram_id": task.telegram_id,
                "text": task.text,
                "status": task.status,
                "short_summary": task.short_summary,
                "summary": task.summary,
                "error": task.error,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
            }
        )
        for task in tasks
    ]
    return SearchTaskPage(data=views, meta=meta)


@app.get("/api/v1/search-tasks/{task_id}", response_model=SearchTaskView)
async def get_search_task(task_id: str) -> SearchTaskView:
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return SearchTaskView.model_validate(to_dict(task))


@app.post("/api/v1/search-tasks/{task_id}/retry", response_model=SearchTaskRetryResponse, status_code=202)
async def retry_task(task_id: str) -> SearchTaskRetryResponse:
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status not in {SearchTaskStatus.FAILED, SearchTaskStatus.DONE}:
        raise HTTPException(status_code=409, detail="Task is still in progress")
    task = reset_to_queue(task_id)
    message = RawSearchTaskMessage(
        task_id=task_id,
        telegram_id=task.telegram_id,
        text=task.text,
        requested_at=datetime.now(timezone.utc),
    )
    publish_raw_task(message)
    return SearchTaskRetryResponse(task_id=task_id, status=task.status)
