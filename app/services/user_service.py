"""User business logic.

Sits between the routers and the repository. Raises domain exceptions
(never HTTP exceptions) so it stays framework-agnostic.
"""

from __future__ import annotations

from app.core.exceptions import EmailAlreadyExistsError, UserNotFoundError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def list_users(self) -> list[User]:
        return self._repository.list()

    def get_user(self, user_id: int) -> User:
        user = self._repository.get(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    def create_user(self, payload: UserCreate) -> User:
        if self._repository.get_by_email(payload.email) is not None:
            raise EmailAlreadyExistsError(payload.email)
        return self._repository.add(
            name=payload.name,
            email=payload.email,
            age=payload.age,
            is_active=payload.is_active,
            role=payload.role,
        )

    def replace_user(self, user_id: int, payload: UserUpdate) -> User:
        """Full update (PUT): apply all provided fields."""
        self._ensure_email_available(payload.email, user_id)
        user = self._repository.update(user_id, payload.model_dump())
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    def patch_user(self, user_id: int, payload: UserUpdate) -> User:
        """Partial update (PATCH): apply only fields the client sent."""
        changes = payload.model_dump(exclude_unset=True)
        self._ensure_email_available(changes.get("email"), user_id)
        user = self._repository.update(user_id, changes)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    def _ensure_email_available(self, email: str | None, user_id: int) -> None:
        """Reject an email already taken by a different user."""
        if email is None:
            return
        existing = self._repository.get_by_email(email)
        if existing is not None and existing.id != user_id:
            raise EmailAlreadyExistsError(email)

    def delete_user(self, user_id: int) -> None:
        if not self._repository.delete(user_id):
            raise UserNotFoundError(user_id)
