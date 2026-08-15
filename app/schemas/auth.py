"""Request/response schemas for authentication."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.user import UserOut


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, examples=["Ada Lovelace"])
    email: EmailStr = Field(..., examples=["ada@example.com"])
    age: int = Field(..., ge=0, examples=[30])
    password: str = Field(..., min_length=8, max_length=128, examples=["s3cret-passw0rd"])


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["ada@example.com"])
    password: str = Field(..., examples=["s3cret-passw0rd"])


class AuthData(BaseModel):
    """Payload returned on successful auth.

    Tokens themselves are delivered via httpOnly cookies; the CSRF token is
    returned here (and in a readable cookie) so the client can echo it back in
    the ``X-CSRF-Token`` header on state-changing requests.
    """

    model_config = ConfigDict(from_attributes=True)

    user: UserOut
    csrf_token: str
