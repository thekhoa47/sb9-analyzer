from fastapi import APIRouter
from .messenger_webhook import router as messenger_webhook_router
from .analyze import router as analyze_router
from .clients import router as clients_router
from .analyzed_properties import router as analyzed_properties_router
from .saved_searches import router as saved_searches_router
from .debug import router as debug_router
from .tasks import router as tasks_router


router = APIRouter(prefix="/api")

router.include_router(messenger_webhook_router)
router.include_router(analyze_router)
router.include_router(clients_router)
router.include_router(analyzed_properties_router)
router.include_router(saved_searches_router)
router.include_router(debug_router)
router.include_router(tasks_router)
