from __future__ import annotations
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.db import get_async_session
from app.core.config import settings
from app.core.cloud_tasks import CloudTasksEnqueuer
from app.services.tasks.saved_search_service import process_saved_search

router = APIRouter(prefix="/tasks", tags=["tasks"])
_enq = CloudTasksEnqueuer()


def _assert_tasks_auth(secret: str | None) -> None:
    if settings.TASKS_SHARED_SECRET and secret != settings.TASKS_SHARED_SECRET:
        raise HTTPException(status_code=401, detail="invalid task secret")


@router.post("/process-saved-search/{saved_search_id}")
async def task_process_saved_search(
    saved_search_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    x_tasks_secret: str | None = Header(default=None),
):
    _assert_tasks_auth(x_tasks_secret)
    count = await process_saved_search(
        saved_search_id=saved_search_id, session=session, enqueuer=_enq
    )
    return {"ok": True, "enqueued_listing_tasks": count}
