from __future__ import annotations
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.cloud_tasks import CloudTasksEnqueuer
from app.services.tasks.process_property_service import process_property
from app.schemas.tasks import PropertyTaskPayload

from app.core.db import get_async_session
from app.core.config import settings

router = APIRouter(prefix="/tasks", tags=["tasks"])
_enq = CloudTasksEnqueuer()


def _assert_tasks_auth(secret: str | None) -> None:
    if settings.TASKS_SHARED_SECRET and secret != settings.TASKS_SHARED_SECRET:
        raise HTTPException(status_code=401, detail="invalid task secret")


@router.post("/process-property")
async def task_process_property(
    payload: PropertyTaskPayload,
    session: AsyncSession = Depends(get_async_session),
    x_tasks_secret: str | None = Header(default=None),
):
    _assert_tasks_auth(x_tasks_secret)
    await process_property(
        payload=payload, session=session, enqueuer=_enq
    )  # function below
    return {"ok": True}
