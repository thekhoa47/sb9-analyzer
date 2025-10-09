from __future__ import annotations
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.config import settings
from app.schemas.tasks import ListingTaskPayload
from app.services.tasks.process_listing_service import process_listing

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _assert_tasks_auth(secret: str | None) -> None:
    if settings.TASKS_SHARED_SECRET and secret != settings.TASKS_SHARED_SECRET:
        raise HTTPException(status_code=401, detail="invalid task secret")


@router.post("/process-listing")
async def task_process_listing(
    payload: ListingTaskPayload,
    session: AsyncSession = Depends(get_async_session),
    x_tasks_secret: str | None = Header(default=None),
):
    _assert_tasks_auth(x_tasks_secret)
    result = await process_listing(payload=payload, session=session)
    return {"ok": True, **result}
