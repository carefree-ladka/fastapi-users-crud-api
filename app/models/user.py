"""User ORM model.

This is the persistence representation the repository/service layers work
with. It is kept separate from the API schemas so the transport contract can
evolve independently from the stored model.
"""
from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    age: Mapped[int]
    is_active: Mapped[bool] = mapped_column(default=False)
    role: Mapped[str] = mapped_column(default="user")
