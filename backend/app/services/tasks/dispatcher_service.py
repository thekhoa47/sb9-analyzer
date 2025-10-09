from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from google.cloud import tasks_v2

from app.models import SavedSearch, Client
from app.core.config import settings
from app.core.cloud_tasks import TaskEnqueuer


async def dispatch_saved_searches(
    *, session: AsyncSession, enqueuer: TaskEnqueuer
) -> int:
    stmt = (
        select(SavedSearch.id)
        .join(SavedSearch.client)
        .where(Client.is_active.is_(True))
    )
    res = await session.execute(stmt)
    ids: list[str] = [row[0] for row in res.all()]

    for sid in ids:
        enqueuer.enqueue_http_task(
            queue=settings.CLOUD_TASKS_QUEUE_SEARCH,
            url=f"{settings.BASE_URL}/tasks/process-saved-search/{sid}",
            method=tasks_v2.HttpMethod.POST,
            headers=(
                {"x-tasks-secret": settings.TASKS_SHARED_SECRET}
                if settings.TASKS_SHARED_SECRET
                else None
            ),
            body={},
            oidc_audience=settings.BASE_URL,
        )
    return len(ids)
