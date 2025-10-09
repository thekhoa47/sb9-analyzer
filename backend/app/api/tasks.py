# app/routers/tasks.py
from fastapi import APIRouter


router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("")
def find_new_listings():
    # Step 1: Query saved_searched table (join & select with saved_search_fields table, join & filter with clients table) for all saved_searches + fields for active clients (clients.)
    return
