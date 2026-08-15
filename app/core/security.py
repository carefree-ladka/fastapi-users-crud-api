"""Security primitives: password hashing, JWT tokens, and CSRF tokens.

Kept framework-agnostic so services can use it without importing FastAPI.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import bcrypt
import jwt

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError

settings = get_settings()

TokenType = Literal["access", "refresh"]

# bcrypt only considers the first 72 bytes of a password.
_BCRYPT_MAX_BYTES = 72


# --- Passwords ---------------------------------------------------------------


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt and return the encoded hash."""
    pw = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Return True if ``password`` matches the stored bcrypt hash."""
    pw = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    try:
        return bcrypt.checkpw(pw, password_hash.encode("utf-8"))
    except ValueError:
        # Malformed hash in storage.
        return False


# --- JWT ---------------------------------------------------------------------


def _create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> tuple[str, str, datetime]:
    """Create a signed JWT. Returns (token, jti, expires_at)."""
    now = datetime.now(UTC)
    expires_at = now + expires_delta
    jti = uuid.uuid4().hex
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, expires_at


def create_access_token(user_id: int, role: str) -> tuple[str, datetime]:
    """Create a short-lived access token carrying the user's role."""
    token, _jti, expires_at = _create_token(
        subject=str(user_id),
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_ttl_minutes),
        extra_claims={"role": role},
    )
    return token, expires_at


def create_refresh_token(user_id: int) -> tuple[str, str, datetime]:
    """Create a long-lived refresh token. Returns (token, jti, expires_at)."""
    return _create_token(
        subject=str(user_id),
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_ttl_days),
    )


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    """Decode and validate a JWT, ensuring it is of the expected type.

    Raises ``AuthenticationError`` on any problem (expired, tampered, wrong
    type) so callers get a consistent 401.
    """
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Token has expired") from exc
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Invalid token") from exc

    if payload.get("type") != expected_type:
        raise AuthenticationError("Invalid token type")
    return payload


# --- CSRF --------------------------------------------------------------------


def generate_csrf_token() -> str:
    """Return a random, URL-safe CSRF token for the double-submit pattern."""
    return secrets.token_urlsafe(32)


def csrf_tokens_match(cookie_token: str | None, header_token: str | None) -> bool:
    """Constant-time comparison of the CSRF cookie and header values."""
    if not cookie_token or not header_token:
        return False
    return secrets.compare_digest(cookie_token, header_token)
