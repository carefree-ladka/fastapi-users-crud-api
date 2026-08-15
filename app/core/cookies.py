"""Helpers for setting and clearing the auth-related cookies.

Three cookies are used:
- ``access_token``  : httpOnly JWT, short-lived.
- ``refresh_token`` : httpOnly JWT, long-lived, scoped to the refresh path.
- ``csrf_token``    : readable by JS (not httpOnly) for the double-submit
                      pattern; echoed back in the ``X-CSRF-Token`` header.
"""

from __future__ import annotations

from typing import Literal, cast

from fastapi import Response

from app.core.config import get_settings

settings = get_settings()

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"
CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"

_SameSite = Literal["lax", "strict", "none"]


def _samesite() -> _SameSite:
    value = settings.cookie_samesite.lower()
    if value not in {"lax", "strict", "none"}:
        value = "lax"
    return cast(_SameSite, value)


def _access_max_age() -> int:
    return settings.access_token_ttl_minutes * 60


def _refresh_max_age() -> int:
    return settings.refresh_token_ttl_days * 24 * 60 * 60


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    refresh_path: str,
) -> None:
    """Attach access, refresh, and CSRF cookies to the response."""
    secure = settings.cookie_secure
    samesite = _samesite()
    domain = settings.cookie_domain

    response.set_cookie(
        ACCESS_COOKIE,
        access_token,
        max_age=_access_max_age(),
        httponly=True,
        path="/",
        secure=secure,
        samesite=samesite,
        domain=domain,
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        max_age=_refresh_max_age(),
        httponly=True,
        # Restrict the refresh cookie to the /auth path.
        path=refresh_path,
        secure=secure,
        samesite=samesite,
        domain=domain,
    )
    response.set_cookie(
        CSRF_COOKIE,
        csrf_token,
        max_age=_refresh_max_age(),
        httponly=False,  # must be readable by the client to echo in the header
        path="/",
        secure=secure,
        samesite=samesite,
        domain=domain,
    )


def clear_auth_cookies(response: Response, refresh_path: str) -> None:
    """Remove all auth cookies (used on logout)."""
    response.delete_cookie(ACCESS_COOKIE, path="/", domain=settings.cookie_domain)
    response.delete_cookie(REFRESH_COOKIE, path=refresh_path, domain=settings.cookie_domain)
    response.delete_cookie(CSRF_COOKIE, path="/", domain=settings.cookie_domain)
