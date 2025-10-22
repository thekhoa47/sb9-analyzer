from fastapi import APIRouter, HTTPException, Request, Response
from app.schemas.auth import LoginIn
from app.services.auth import (
    verify_credentials,
    sign_session,
    verify_session,
    set_session_cookie,
    clear_session_cookie,
)
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", status_code=204)
async def login(body: LoginIn, response: Response):
    if not verify_credentials(body.username, body.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = sign_session(body.username)
    set_session_cookie(response, token)


@router.get("/session", status_code=204)
async def session(request: Request):
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token or not verify_session(token):
        raise HTTPException(status_code=401, detail="Not authenticated")


@router.post("/logout", status_code=204)
async def logout(response: Response):
    clear_session_cookie(response)
