"""API request/response schemas for users (Pydantic v2)."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    name: str = Field(..., min_length=1, examples=["Aarav Sharma"])
    email: str = Field(..., examples=["aarav.sharma@example.com"])
    age: int = Field(..., ge=0, examples=[28])
    is_active: bool = False
    role: str = "user"


class UserCreate(UserBase):
    """Payload for creating a user."""


class UserUpdate(BaseModel):
    """Payload for updating a user.

    All fields optional so the same schema serves PUT and PATCH. For PATCH,
    use ``exclude_unset=True`` so only provided fields are applied.
    """

    name: str | None = None
    email: str | None = None
    age: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    role: str | None = None


class UserOut(UserBase):
    """User representation returned to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: int
