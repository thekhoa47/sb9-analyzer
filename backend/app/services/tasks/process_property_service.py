from sqlalchemy.ext.asyncio import AsyncSession
from google.cloud import tasks_v2

from app.core.cloud_tasks import TaskEnqueuer
from app.core.config import settings
from app.schemas.tasks import ListingTaskPayload, PropertyTaskPayload
from app.services.sb9 import get_property_geoms
from app.services.sb9_2 import find_house_containment_split_feet


async def process_property(
    *, payload: PropertyTaskPayload, session: AsyncSession, enqueuer: TaskEnqueuer
):
    try:
        property_id = payload.property_id
        listing_id = payload.listing_id
        saved_search_id = payload.saved_search_id
        property_with_geoms = await get_property_geoms(property_id, session)
        await find_house_containment_split_feet(
            session,
            property_id=property_id,
            parcel_xy=property_with_geoms.parcel,
            house_xy=property_with_geoms.house,
        )
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    enqueuer.enqueue_http_task(
        queue=settings.CLOUD_TASKS_QUEUE_LISTING,
        url=f"{settings.BASE_URL}/tasks/process-listing",
        method=tasks_v2.HttpMethod.POST,
        headers=(
            {"x-tasks-secret": settings.TASKS_SHARED_SECRET}
            if settings.TASKS_SHARED_SECRET
            else None
        ),
        body=ListingTaskPayload(
            listing_id=listing_id, saved_search_id=saved_search_id
        ).model_dump(mode="json"),
        oidc_audience=settings.BASE_URL,
    )
