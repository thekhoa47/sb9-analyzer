from __future__ import annotations
from fastapi import APIRouter

from .entry import router as cron_entry_router
from .dispatcher import router as dispatcher_router
from .saved_search import router as saved_search_router
from .process_property import router as process_property_router
from .process_listing import router as process_listing_router

router = APIRouter()
router.include_router(cron_entry_router)  # e.g., prefix="/cron" inside entry.py
router.include_router(dispatcher_router)  # e.g., prefix="/tasks"
router.include_router(saved_search_router)  # e.g., prefix="/tasks"
router.include_router(process_property_router)  # e.g., prefix="/tasks"
router.include_router(process_listing_router)  # e.g., prefix="/tasks"
