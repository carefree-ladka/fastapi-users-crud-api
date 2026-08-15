"""Database engine, session factory, and session dependency.

Uses SQLAlchemy 2.0 with a local SQLite database by default. The connection
string is configurable via the ``DATABASE_URL`` setting so the same code can
point at Postgres/MySQL later without changes to the repository layer.
"""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# ``check_same_thread`` is only needed for SQLite, which otherwise forbids
# sharing a connection across threads (uvicorn runs sync endpoints in a pool).
_connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(settings.database_url, connect_args=_connect_args)

# ``expire_on_commit=False`` keeps attributes accessible after commit so ORM
# instances can still be serialized by the response model.
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
)


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a request-scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
