"""Domain-level exceptions.

Services raise these framework-agnostic errors; the web layer translates them
into consistent HTTP error responses via the handler registered in
``app.main``. Each error carries an HTTP ``status_code``, a machine-readable
``code``, and a human-readable message.
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base class for domain errors."""

    status_code: int = 400
    code: str = "app_error"

    def __init__(self, message: str, *, details: Any | None = None) -> None:
        self.message = message
        self.details = details
        super().__init__(message)


class UserNotFoundError(AppError):
    """Raised when a user cannot be found by id."""

    status_code = 404
    code = "user_not_found"

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        super().__init__(f"User {user_id} not found")


class EmailAlreadyExistsError(AppError):
    """Raised when creating/updating a user with an email already in use."""

    status_code = 409
    code = "email_already_exists"

    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"A user with email '{email}' already exists")
