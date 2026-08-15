"""Database initialization and seeding.

Creates tables and, if the users table is empty, inserts the seed data (each
seeded user gets a default password hash). Called once on application startup.
"""

from __future__ import annotations

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models.refresh_token import RefreshToken  # noqa: F401  (register table)
from app.models.user import User  # noqa: F401  (register table)
from app.repositories.user_repository import seed_users

# Default password assigned to every seeded user (local/demo only).
SEED_PASSWORD = "password123"


def init_db() -> None:
    """Create tables and seed initial data when the users table is empty."""
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        already_seeded = db.scalar(select(User).limit(1)) is not None
        if not already_seeded:
            users = seed_users()
            hashed = hash_password(SEED_PASSWORD)
            for user in users:
                user.hashed_password = hashed
            db.add_all(users)
            db.commit()
