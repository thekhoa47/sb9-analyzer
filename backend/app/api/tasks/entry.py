from __future__ import annotations
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException
from google.cloud import tasks_v2

from app.core.config import settings
from app.core.cloud_tasks import CloudTasksEnqueuer

router = APIRouter(prefix="/cron", tags=["cron"])
_enq = CloudTasksEnqueuer()


@router.post("/enqueue-dispatcher")
async def enqueue_dispatcher(
    x_cron_secret: Annotated[str | None, Header(alias="x-cron-secret")] = None,
):
    # Only enforce when CRON_SECRET is set
    if settings.CRON_SECRET and x_cron_secret != settings.CRON_SECRET:
        raise HTTPException(status_code=401, detail="invalid secret")

    _enq.enqueue_http_task(
        queue=settings.CLOUD_TASKS_QUEUE_DISPATCHER,
        url=f"{settings.BASE_URL}/tasks/dispatch-saved-searches",
        method=tasks_v2.HttpMethod.POST,  # or just omit
        headers=(
            {"x-tasks-secret": settings.TASKS_SHARED_SECRET}
            if settings.TASKS_SHARED_SECRET
            else None
        ),
        body={},
        oidc_audience=settings.BASE_URL,
    )
    return {"ok": True, "enqueued": 1}
