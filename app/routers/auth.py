"""Authentication endpoints: register, login, refresh, logout, me.

Tokens are delivered as httpOnly cookies. State-changing endpoints that rely on
the ambient session cookie (refresh, logout) are CSRF-protected via the
double-submit pattern; register/login are exempt (no session exists yet).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status

from app.core.config import get_settings
from app.core.cookies import REFRESH_COOKIE, clear_auth_cookies, set_auth_cookies
from app.dependencies.auth import csrf_protect, get_auth_service, get_current_user
from app.models.user import User
from app.schemas.auth import AuthData, LoginRequest, RegisterRequest
from app.schemas.response import APIResponse, MessageResponse
from app.schemas.user import UserOut
from app.services.auth_service import AuthService, IssuedTokens

router = APIRouter(prefix="/auth", tags=["auth"])

settings = get_settings()

# The refresh cookie is scoped to the /auth path so it is sent to both the
# refresh and logout endpoints, but not to the rest of the API.
REFRESH_PATH = f"{settings.api_v1_prefix}/auth"


def _auth_response(response: Response, tokens: IssuedTokens, message: str) -> APIResponse[AuthData]:
    set_auth_cookies(
        response,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        csrf_token=tokens.csrf_token,
        refresh_path=REFRESH_PATH,
    )
    return APIResponse(
        message=message,
        data=AuthData(user=UserOut.model_validate(tokens.user), csrf_token=tokens.csrf_token),
    )


@router.post(
    "/register",
    response_model=APIResponse[AuthData],
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> APIResponse[AuthData]:
    tokens = service.register(payload)
    return _auth_response(response, tokens, "Registration successful")


@router.post("/login", response_model=APIResponse[AuthData])
def login(
    payload: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> APIResponse[AuthData]:
    tokens = service.login(payload)
    return _auth_response(response, tokens, "Login successful")


@router.post(
    "/refresh",
    response_model=APIResponse[AuthData],
    dependencies=[Depends(csrf_protect)],
)
def refresh(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> APIResponse[AuthData]:
    token = request.cookies.get(REFRESH_COOKIE)
    tokens = service.refresh(token or "")
    return _auth_response(response, tokens, "Token refreshed")


@router.post(
    "/logout",
    response_model=MessageResponse,
    dependencies=[Depends(csrf_protect)],
)
def logout(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    service.logout(request.cookies.get(REFRESH_COOKIE))
    clear_auth_cookies(response, refresh_path=REFRESH_PATH)
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=APIResponse[UserOut])
def me(current_user: User = Depends(get_current_user)) -> APIResponse[UserOut]:
    return APIResponse(
        message="Current user",
        data=UserOut.model_validate(current_user),
    )
