# app/jobs_lock.py
from contextlib import contextmanager
from sqlalchemy import text
from .core import SessionLocal

LOCK_KEY = 0x5B9_0001  # arbitrary 64-bit int; keep stable


@contextmanager
def poll_lock(timeout_seconds: int = 0):
    """
    Postgres advisory lock. Returns immediately if cannot acquire (timeout=0).
    """
    db = SessionLocal()
    try:
        acquired = db.execute(
            text("SELECT pg_try_advisory_lock(:k)"), {"k": LOCK_KEY}
        ).scalar()
        if not acquired:
            yield False
            return
        yield True
    finally:
        # Release only if we hold it
        try:
            db.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": LOCK_KEY})
            db.commit()
        except Exception:
            pass
        db.close()
