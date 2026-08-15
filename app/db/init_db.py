"""Database initialization and seeding.

Creates tables and, if the users table is empty, inserts the seed data. Called
once on application startup.
"""
from __future__ import annotations

from sqlalchemy import select

from app.db.session import Base, SessionLocal, engine
from app.models.user import User  # noqa: F401  (ensures the model is registered)
from app.repositories.user_repository import seed_users


def init_db() -> None:
    """Create tables and seed initial data when the users table is empty."""
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        already_seeded = db.scalar(select(User).limit(1)) is not None
        if not already_seeded:
            db.add_all(seed_users())
            db.commit()
