from fastapi import APIRouter
from .messenger_webhook import router as messenger_webhook_router
from .tasks import router as tasks_router
from .analyze import router as analyze_router
from .clients import router as clients_router
from .prep_image import router as prep_image_router
from .results import router as results_router
from .saved_searches import router as saved_searches_router
from .debug import router as debug_router


router = APIRouter(prefix="/api")

router.include_router(messenger_webhook_router)
router.include_router(tasks_router)
router.include_router(analyze_router)
router.include_router(clients_router)
router.include_router(prep_image_router)
router.include_router(results_router)
router.include_router(saved_searches_router)
router.include_router(debug_router)
