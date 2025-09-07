# app/routers/tasks.py
from fastapi import APIRouter, Header, HTTPException
from app.core import settings
from app.jobs import trigger_poll_once, get_scheduler_status

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/poll")
def run_poll(x_task_key: str | None = Header(default=None, alias="X-Task-Key")):
    if settings.TASK_KEY and x_task_key != settings.TASK_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    trigger_poll_once()
    return get_scheduler_status()
