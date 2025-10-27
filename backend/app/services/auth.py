from datetime import datetime
from typing import Optional
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import bcrypt
from fastapi import Response


from app.core.config import settings


# Hardcoded minimal session settings for localhost dev


_serializer = URLSafeTimedSerializer(settings.SECRET_KEY)


def sign_session(username: str) -> str:
    return _serializer.dumps({"u": username, "iat": int(datetime.utcnow().timestamp())})


def verify_session(token: str) -> Optional[str]:
    try:
        data = _serializer.loads(token, max_age=settings.SESSION_AGE)
        return data.get("u") or None
    except (BadSignature, SignatureExpired):
        return None


def verify_credentials(username: str, password: str) -> bool:
    if username != settings.ADMIN_USERNAME:
        return False
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            settings.ADMIN_PASSWORD_HASH.encode("utf-8"),
        )
    except Exception:
        return False


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,  # "HannahAdmin"
        value=token,  # whatever you sign
        httponly=True,
        secure=True,
        samesite="Lax",  # or "None" if you're doing cross-site POSTs with credentials
        domain=".hannahanhdao.com",  # <-- now this matters
        path="/",
        max_age=settings.SESSION_AGE,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.SESSION_COOKIE_NAME, path="/")
