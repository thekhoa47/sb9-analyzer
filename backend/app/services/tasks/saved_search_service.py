from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from google.cloud import tasks_v2
from openai import AsyncOpenAI
from pydantic import ValidationError
from datetime import datetime
from uuid import UUID

from app.models import SavedSearch, SavedSearchMatch, Listing, Property
from app.core.config import settings
from app.core.cloud_tasks import TaskEnqueuer
from app.schemas.openai import FoundListing, FindListingsResult
from app.schemas.tasks import PropertyTaskPayload

_oai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


def _index_fields(
    saved_search: SavedSearch,
) -> tuple[
    str | None,  # beds_min
    str | None,  # baths_min
    str | None,  # max_price
    str | None,  # analysis_note
    str | None,  # city
    str | None,  # zip
    str | None,  # property_sub_type
    str | None,  # within_radius
    str | None,  # garage_spaces
    str | None,  # lot_size
    str | None,  # living_area
]:
    beds_min = saved_search.beds_min
    baths_min = saved_search.baths_min
    max_price = saved_search.max_price
    map: dict[str, str] = {}
    for f in saved_search.fields:
        key = f.search_field
        val = f.value
        if key and val is not None and key not in map:
            map[key] = val

    city = map.get("city")
    zip_code = map.get("zip")
    property_subtype = map.get("property_sub_type")
    within_radius = map.get("within_radius")
    garage_spaces = map.get("garage_spaces")
    lot_size = map.get("lot_size")
    living_area = map.get("living_area")

    return (
        beds_min,
        baths_min,
        max_price,
        city,
        zip_code,
        property_subtype,
        within_radius,
        garage_spaces,
        lot_size,
        living_area,
    )


def _make_find_listings_prompt(saved_search: SavedSearch) -> str:
    (
        beds_min,
        baths_min,
        max_price,
        city,
        zip_code,
        property_subtype,
        within_radius,
        garage_spaces,
        lot_size,
        living_area,
    ) = _index_fields(saved_search)

    # Build the human-readable criteria (minimal guards; blanks are fine)
    criteria = (
        "Find currently For Sale listings on Zillow that satisfy the requirements:\n"
        f"Must be {property_subtype} with minimum {beds_min} beds, and {baths_min} baths and maximum ${max_price}.\n"
        f"Located within Orange County (Aliso Viejo,Anaheim,Brea,Buena Park,Costa Mesa,Cypress,Dana Point,Fountain Valley,Fullerton,Garden Grove,Huntington Beach,Irvine,La Habra,La Palma,Laguna Beach,Laguna Hills,Laguna Niguel,Laguna Woods,Lake Forest,Los Alamitos,Mission Viejo,Newport Beach,Orange,Placentia,Rancho Santa Margarita,San Clemente,San Juan Capistrano,Santa Ana,Seal Beach,Stanton,Tustin,Villa Park,Westminster,Yorba Linda).\n",
        f"Preferably: {garage_spaces} garage spaces, minimum lot size {lot_size} sqft, and minimum living area {living_area} sqft.\n",
    )

    schema = (
        '{ "listings": ['
        '{"source":"zillow","external_id":str|None,"url":str,'
        '"address_line1":"str","address_line2":str|None,'
        '"city":str,"state":str,"zip":str,'
        '"listing_price":number,"listing_date":datetime ISO 8601,'
        '"status":"ACTIVE",'
        '"bedrooms":int|None,"bathrooms":float|None,"year_built":int|None}'
        "]}"
    )

    return (
        f"{criteria}\n"
        "Return STRICTLY valid JSON ONLY in the exact schema below (no prose, no code fences):\n"
        f"{schema}\n\n"
        "DO NOT MAKE UP ANY FAKE LISTING. DO NOT GIVE ME SOLD OR OFF MARKET LISTINGS\n"
        "For listing_date use the Days on Zillow to estimate the date.\n"
        "DO NOT put City, State, Zip in address line 1.\n"
        'If nothing found, return exactly {"listings":[]}.'
    )


async def _ask_openai_for_listings(prompt: str) -> FindListingsResult:
    resp = await _oai.responses.create(
        model="gpt-4o-mini", tools=[{"type": "web_search"}], input=prompt
    )

    try:
        payload = json.loads(resp.output_text)
    except Exception:
        return FindListingsResult(listings=[])

    try:
        return FindListingsResult.model_validate(payload)
    except ValidationError:
        return FindListingsResult(listings=[])


# TODO: Move to Listing service?
async def _get_or_create_listing(
    session: AsyncSession, item: FoundListing, property: Property
) -> Listing:
    q = select(Listing).where(
        Listing.source == item.source,
        Listing.external_id == item.external_id,
    )
    existing = (await session.execute(q)).scalar_one_or_none()
    if existing:
        existing.listing_price = item.listing_price or existing.listing_price
        existing.listing_date = item.listing_date or existing.listing_date
        existing.status = item.status or existing.status
        return existing
    row = Listing(
        property_id=property.id,
        source=item.source,
        external_id=item.external_id,
        status=item.status or "ACTIVE",
        is_active=(item.status == "ACTIVE"),
        last_seen_at=datetime.now(),
        listing_price=item.listing_price,
        listing_date=item.listing_date,
    )
    session.add(row)
    try:
        await session.flush()  # surfaces IntegrityError if unique constraint hits
        return row
    except IntegrityError:
        await (
            session.rollback()
        )  # or use a savepoint with begin_nested() if you have other pending work
        return (await session.execute(q)).scalar_one()


# TODO: Move to property service?
async def _get_or_create_property(
    session: AsyncSession, item: FoundListing
) -> Property:
    address_line2 = (item.address_line2 or "").strip()
    base_filters = [
        Property.address_line1 == item.address_line1,
        Property.city == item.city,
        Property.state == item.state,
        Property.zip == item.zip,
    ]
    addr2_filter = (
        Property.address_line2.is_(None)
        if not address_line2
        else Property.address_line2 == address_line2
    )

    q = select(Property).where(*base_filters, addr2_filter)

    existing = (await session.execute(q)).scalar_one_or_none()

    if existing:
        return existing

    row = Property(
        address_line1=item.address_line1,
        address_line2=item.address_line2,
        city=item.city,
        state=item.state,
        zip=item.zip,
        bedrooms=item.bedrooms,
        bathrooms=item.bathrooms,
        year_built=item.year_built,
    )
    session.add(row)
    try:
        await session.flush()  # surfaces IntegrityError if unique constraint hits
        return row
    except IntegrityError:
        await (
            session.rollback()
        )  # or use a savepoint with begin_nested() if you have other pending work
        return (await session.execute(q)).scalar_one()


async def _get_or_create_saved_search_match(
    session: AsyncSession, ssid: UUID, lid: UUID
) -> SavedSearchMatch:
    q = select(SavedSearchMatch).where(
        SavedSearchMatch.listing_id == lid,
        SavedSearchMatch.saved_search_id == ssid,
    )
    existing = (await session.execute(q)).scalar_one_or_none()
    if existing:
        return existing
    row = SavedSearchMatch(listing_id=lid, saved_search_id=ssid)
    session.add(row)


async def process_saved_search(
    *, saved_search_id: UUID, session: AsyncSession, enqueuer: TaskEnqueuer
) -> int:
    ss: SavedSearch | None = await session.get(
        SavedSearch,
        saved_search_id,
        options=[
            selectinload(SavedSearch.client),
            selectinload(SavedSearch.fields),
            selectinload(SavedSearch.matches),
        ],
    )
    if not ss or not ss.client or not ss.client.is_active:
        return 0

    prompt = _make_find_listings_prompt(ss)
    found = await _ask_openai_for_listings(prompt)
    if not found.listings:
        return 0
    new_listing_ids = []

    for item in found.listings:
        try:
            prop = await _get_or_create_property(session, item)
            listing = await _get_or_create_listing(session, item, property=prop)
            await _get_or_create_saved_search_match(session, ss.id, listing.id)
            new_listing_ids.append(listing.id)
            await session.flush()
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        enqueuer.enqueue_http_task(
            queue=settings.CLOUD_TASKS_QUEUE_PROPERTY,
            url=f"{settings.BASE_URL}/tasks/process-property",
            method=tasks_v2.HttpMethod.POST,
            headers=(
                {"x-tasks-secret": settings.TASKS_SHARED_SECRET}
                if settings.TASKS_SHARED_SECRET
                else None
            ),
            body=PropertyTaskPayload(
                saved_search_id=ss.id, listing_id=listing.id, property_id=prop.id
            ).model_dump(mode="json"),
            oidc_audience=settings.BASE_URL,
        )

    return len(new_listing_ids)
