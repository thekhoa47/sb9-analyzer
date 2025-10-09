from __future__ import annotations
from fastapi.encoders import jsonable_encoder
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from openai import AsyncOpenAI
from pydantic import ValidationError
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping


from app.models import (
    Listing,
    SavedSearch,
    SearchListingAnalysis,
    Property,
)
from app.core.config import settings
from app.schemas.openai import ListingAnalysisJSON
from app.schemas.tasks import ListingTaskPayload
from app.services.notification import notify_client_for_good_listing

_oai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
encoders = {
    WKBElement: lambda g: mapping(to_shape(g)),
}

# ---- Prompts live here (business logic) ----
LISTING_ANALYZE_SYSTEM = (
    "You are a valuation analyst. Given (1) listing facts and (2) client preferences, "
    "Analyze and return in provided JSON format."
    "llm_analysis: detailed analysis of price fairness, comps, monthly payment estimates, school zone, and analysis note (from saved search).\n"
    "llm_summary: concise summary of the analysis. Aim for maximum 2, 3 sentences.\n"
    "verdict: 'good' if this listing is a strong match for the saved search, 'neutral' if it's okay but not great, 'bad' if it's a poor match.\n"
)


def _make_listing_analyze_prompt(listing: Listing, saved_search: SavedSearch) -> str:
    bundle = {
        "listing": {
            "address_line1": listing.property.address_line1,
            "address_line2": listing.property.address_line2,
            "city": listing.property.city,
            "state": listing.property.state,
            "zip": listing.property.zip,
            "price": listing.listing_price,
            "beds": listing.property.bedrooms,
            "baths": listing.property.bathrooms,
            "sb9_possible": listing.property.analysis.sb9_possible,
            "adu_possible": listing.property.analysis.adu_possible,
        },
        "client_preferences": {
            "beds_min": saved_search.beds_min,
            "baths_min": saved_search.baths_min,
            "max_price": saved_search.max_price,
            "analysis_note": saved_search.analysis_note,
        },
    }
    safe = jsonable_encoder(bundle)  # Decimal→float, UUID→str, datetime→iso, etc.

    return (
        "Inputs:\n" + json.dumps(safe, ensure_ascii=False) + "\n\n"
        "Return JSON only with this schema:\n"
        "{"
        '"llm_analysis":"text",'
        '"llm_summary":"text",'
        '"verdict":"good|neutral|bad",'
        "}"
    )


# ---- OpenAI helpers ----
async def _ask_openai_listing_analyze(prompt: str) -> ListingAnalysisJSON:
    resp = await _oai.responses.create(
        model="gpt-4o-mini", tools=[{"type": "web_search"}], input=prompt
    )

    try:
        payload = json.loads(resp.output_text)
        return ListingAnalysisJSON.model_validate(payload)
    except (json.JSONDecodeError, ValidationError):
        return ListingAnalysisJSON(
            llm_analysis="Cannot gather enough information to analyze properly.",
            llm_summary="Cannot draw a conclusion due to lack of information.",
            verdict="neutral",
        )


# ---- Main Task C entry ----
async def process_listing(
    *, payload: ListingTaskPayload, session: AsyncSession
) -> dict[str, str]:
    listing: Listing | None = await session.get(
        Listing,
        payload.listing_id,
        options=[joinedload(Listing.property).joinedload(Property.analysis)],
    )
    saved_search: SavedSearch | None = await session.get(
        SavedSearch, payload.saved_search_id, options=[selectinload(SavedSearch.fields)]
    )
    if not listing or not saved_search:
        return {"message": "Invalid listing or saved_search."}

    prompt = _make_listing_analyze_prompt(listing, saved_search)
    response = await _ask_openai_listing_analyze(prompt)

    sla_row = SearchListingAnalysis(
        saved_search_id=saved_search.id,
        listing_id=listing.id,
        property_analysis_id=listing.property.analysis.id,
        criteria_snapshot=jsonable_encoder(saved_search.to_dict()),
        listing_snapshot=jsonable_encoder(listing.to_dict(), custom_encoder=encoders),
        llm_analysis=response.llm_analysis,
        llm_summary=response.llm_summary,
        verdict=response.verdict,
    )
    session.add(sla_row)
    await session.commit()

    # 3) notify if "good" (immediate send w/ simple idempotency)
    if sla_row.verdict == "good":
        await notify_client_for_good_listing(
            session=session,
            saved_search_id=payload.saved_search_id,
            listing_id=payload.listing_id,
            search_listing_analysis_id=sla_row.id,
        )

    return {"listing_processed": str(listing.id)}
