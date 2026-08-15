"""Auth dependencies: current user, role guards, and CSRF protection."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.cookies import ACCESS_COOKIE, CSRF_COOKIE, CSRF_HEADER
from app.core.exceptions import AuthenticationError, CSRFError, PermissionDeniedError
from app.core.security import csrf_tokens_match, decode_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db), RefreshTokenRepository(db))


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from the access-token cookie."""
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise AuthenticationError("Not authenticated")

    payload = decode_token(token, expected_type="access")
    user = UserRepository(db).get(int(payload["sub"]))
    if user is None or not user.is_active:
        raise AuthenticationError("User is inactive or no longer exists")
    return user


def require_roles(*roles: str) -> Callable[[User], User]:
    """Build a dependency that requires the current user to have one of ``roles``."""

    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise PermissionDeniedError(f"Requires one of roles: {', '.join(roles)}")
        return current_user

    return _checker


# Convenience guard for admin-only endpoints.
require_admin = require_roles("admin")


def csrf_protect(request: Request) -> None:
    """Enforce the double-submit CSRF check on state-changing requests.

    The client must send the value of the readable ``csrf_token`` cookie back
    in the ``X-CSRF-Token`` header. Safe methods are never checked.
    """
    if request.method in {"GET", "HEAD", "OPTIONS", "TRACE"}:
        return
    cookie_token = request.cookies.get(CSRF_COOKIE)
    header_token = request.headers.get(CSRF_HEADER)
    if not csrf_tokens_match(cookie_token, header_token):
        raise CSRFError()
