"""Authentication business logic.

Handles registration, credential verification, and the lifecycle of access +
refresh tokens (issue, rotate, revoke). Framework-agnostic: it returns tokens
and user objects; the web layer is responsible for setting cookies.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.exceptions import AuthenticationError, EmailAlreadyExistsError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_csrf_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest


@dataclass
class IssuedTokens:
    """Bundle returned when a session is created or refreshed."""

    user: User
    access_token: str
    refresh_token: str
    csrf_token: str


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        refresh_tokens: RefreshTokenRepository,
    ) -> None:
        self._users = users
        self._refresh_tokens = refresh_tokens

    # --- Registration & login ------------------------------------------------

    def register(self, payload: RegisterRequest) -> IssuedTokens:
        if self._users.get_by_email(payload.email) is not None:
            raise EmailAlreadyExistsError(payload.email)
        user = self._users.add(
            name=payload.name,
            email=payload.email,
            age=payload.age,
            is_active=True,
            role="user",  # new registrations are always regular users
            hashed_password=hash_password(payload.password),
        )
        return self._issue_tokens(user)

    def login(self, payload: LoginRequest) -> IssuedTokens:
        user = self._users.get_by_email(payload.email)
        # Verify a hash even when the user is missing to reduce timing leaks.
        stored_hash = user.hashed_password if user else ""
        if not verify_password(payload.password, stored_hash) or user is None:
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("Account is inactive")
        return self._issue_tokens(user)

    # --- Session lifecycle ---------------------------------------------------

    def refresh(self, refresh_token: str) -> IssuedTokens:
        """Rotate a refresh token: validate, revoke the old, issue a new pair."""
        payload = decode_token(refresh_token, expected_type="refresh")
        jti = payload.get("jti")
        stored = self._refresh_tokens.get(jti) if jti else None
        if stored is None or stored.revoked:
            raise AuthenticationError("Refresh token is no longer valid")

        # SQLite returns naive datetimes; normalize to UTC before comparing.
        expires_at = stored.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < datetime.now(UTC):
            raise AuthenticationError("Refresh token has expired")

        user = self._users.get(int(payload["sub"]))
        if user is None or not user.is_active:
            raise AuthenticationError("User is no longer active")

        # Rotate: the old refresh token can never be used again.
        self._refresh_tokens.revoke(stored.jti)
        return self._issue_tokens(user)

    def logout(self, refresh_token: str | None) -> None:
        """Revoke the presented refresh token (best effort)."""
        if not refresh_token:
            return
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except AuthenticationError:
            return
        jti = payload.get("jti")
        if jti:
            self._refresh_tokens.revoke(jti)

    # --- Helpers -------------------------------------------------------------

    def _issue_tokens(self, user: User) -> IssuedTokens:
        access_token, _ = create_access_token(user.id, user.role)
        refresh_token, jti, expires_at = create_refresh_token(user.id)
        self._refresh_tokens.add(jti=jti, user_id=user.id, expires_at=expires_at)
        return IssuedTokens(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            csrf_token=generate_csrf_token(),
        )
