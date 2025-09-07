# app/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings


# Declarative base for all models
class Base(DeclarativeBase):
    pass


# Engine (reuse one engine per process)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

# Session factory (thread-safe factory; sessions are not thread-safe)
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db():
    """FastAPI dependency to yield a scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
