from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.db import get_async_session
from app.schemas.property_analysis import PropertyAnalysisOut
from app.services.property_analysis.property_analysis_service import (
    analyze_property_from_address,
)

router = APIRouter(
    prefix="/analyze-property-from-address", tags=["analyze-property-from-address"]
)


class AnalyzeIn(BaseModel):
    address_in: str


@router.post("", response_model=PropertyAnalysisOut)
async def analyze_from_address(
    body: AnalyzeIn,
    session: AsyncSession = Depends(get_async_session),
):
    return await analyze_property_from_address(
        session=session, address_in=body.address_in
    )
