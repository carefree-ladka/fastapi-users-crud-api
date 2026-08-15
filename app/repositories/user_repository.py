"""Database-backed user repository.

Encapsulates all data access for users behind a small method surface. Swapping
the underlying database (SQLite -> Postgres, etc.) only requires changing the
connection string; this class stays the same.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def seed_users() -> list[User]:
    """Return the initial set of users used to populate an empty database."""
    return [
        User(
            name="Aarav Sharma",
            email="aarav.sharma@example.com",
            age=28,
            is_active=True,
            role="user",
        ),
        User(
            name="Priya Singh",
            email="priya.singh@example.com",
            age=25,
            is_active=True,
            role="admin",
        ),
        User(
            name="Rahul Verma",
            email="rahul.verma@example.com",
            age=32,
            is_active=False,
            role="user",
        ),
        User(
            name="Ananya Gupta",
            email="ananya.gupta@example.com",
            age=27,
            is_active=True,
            role="moderator",
        ),
        User(
            name="Vikram Patel",
            email="vikram.patel@example.com",
            age=35,
            is_active=True,
            role="user",
        ),
        User(
            name="Neha Kapoor",
            email="neha.kapoor@example.com",
            age=24,
            is_active=False,
            role="user",
        ),
        User(
            name="Arjun Mehta",
            email="arjun.mehta@example.com",
            age=30,
            is_active=True,
            role="admin",
        ),
        User(
            name="Sneha Reddy", email="sneha.reddy@example.com", age=29, is_active=True, role="user"
        ),
        User(
            name="Karan Malhotra",
            email="karan.malhotra@example.com",
            age=31,
            is_active=False,
            role="user",
        ),
        User(
            name="Ishita Joshi",
            email="ishita.joshi@example.com",
            age=26,
            is_active=True,
            role="moderator",
        ),
    ]


class UserRepository:
    """Data access for users, backed by a SQLAlchemy session."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list(self) -> list[User]:
        return list(self._db.scalars(select(User).order_by(User.id)))

    def get(self, user_id: int) -> User | None:
        return self._db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self._db.scalar(select(User).where(User.email == email))

    def add(self, name: str, email: str, age: int, is_active: bool, role: str) -> User:
        user = User(name=name, email=email, age=age, is_active=is_active, role=role)
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def update(self, user_id: int, changes: dict[str, object]) -> User | None:
        user = self.get(user_id)
        if user is None:
            return None
        for field, value in changes.items():
            if hasattr(user, field):
                setattr(user, field, value)
        self._db.commit()
        self._db.refresh(user)
        return user

    def delete(self, user_id: int) -> bool:
        user = self.get(user_id)
        if user is None:
            return False
        self._db.delete(user)
        self._db.commit()
        return True
