"""Standard API response envelopes.

Every endpoint returns a consistent, human-readable shape:

Success::

    {"success": true, "message": "...", "data": {...}}

Error::

    {"success": false, "message": "...", "error": {"code": "...", "details": ...}}
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Envelope for successful responses that carry data."""

    success: bool = True
    message: str
    data: T | None = None


class MessageResponse(BaseModel):
    """Envelope for successful responses that carry only a message."""

    success: bool = True
    message: str


class ErrorDetail(BaseModel):
    code: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    """Envelope for error responses."""

    success: bool = False
    message: str
    error: ErrorDetail
