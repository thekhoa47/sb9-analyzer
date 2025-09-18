# app/core/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api import router as api_router
import logging

log = logging.getLogger("sb9")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    except Exception as e:
        log.exception("[SB9] Startup error: %s: %s", type(e).__name__, e)
        yield
    finally:
        pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(title="sb9-analyzer backend", version="0.3.0", lifespan=lifespan)

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://0.0.0.0:3000",
            "https://anhdao.vercel.app",
            "https://www.hannahanhdao.com",
            "https://hannahanhdao.com",
        ],
        # Allow Vercel preview deployments too:
        allow_origin_regex=r"^https://anhdao-.*\.vercel\.app$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router)

    return app
