"""User endpoints (thin controllers).

Controllers only translate HTTP <-> service calls and wrap results in the
standard response envelope. All business logic lives in UserService; error
handling is done by the global exception handlers.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.core.exceptions import PermissionDeniedError
from app.dependencies.auth import csrf_protect, get_current_user, require_admin
from app.dependencies.user import get_user_service
from app.models.user import User
from app.schemas.response import APIResponse, MessageResponse
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=APIResponse[list[UserOut]])
def list_users(
    service: UserService = Depends(get_user_service),
    _admin: User = Depends(require_admin),
) -> APIResponse[list[UserOut]]:
    users = service.list_users()
    return APIResponse(
        message=f"Retrieved {len(users)} user(s)",
        data=[UserOut.model_validate(u) for u in users],
    )


@router.get("/{user_id}", response_model=APIResponse[UserOut])
def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
) -> APIResponse[UserOut]:
    # Admins can view anyone; regular users may only view themselves.
    if current_user.role != "admin" and current_user.id != user_id:
        raise PermissionDeniedError("You can only view your own account")
    user = service.get_user(user_id)
    return APIResponse(
        message=f"Retrieved user {user_id}",
        data=UserOut.model_validate(user),
    )


@router.post(
    "",
    response_model=APIResponse[UserOut],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin), Depends(csrf_protect)],
)
def create_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
) -> APIResponse[UserOut]:
    user = service.create_user(payload)
    return APIResponse(
        message=f"User '{user.name}' created successfully",
        data=UserOut.model_validate(user),
    )


@router.put(
    "/{user_id}",
    response_model=APIResponse[UserOut],
    dependencies=[Depends(require_admin), Depends(csrf_protect)],
)
def replace_user(
    user_id: int,
    payload: UserUpdate,
    service: UserService = Depends(get_user_service),
) -> APIResponse[UserOut]:
    user = service.replace_user(user_id, payload)
    return APIResponse(
        message=f"User {user_id} replaced successfully",
        data=UserOut.model_validate(user),
    )


@router.patch(
    "/{user_id}",
    response_model=APIResponse[UserOut],
    dependencies=[Depends(require_admin), Depends(csrf_protect)],
)
def patch_user(
    user_id: int,
    payload: UserUpdate,
    service: UserService = Depends(get_user_service),
) -> APIResponse[UserOut]:
    user = service.patch_user(user_id, payload)
    return APIResponse(
        message=f"User {user_id} updated successfully",
        data=UserOut.model_validate(user),
    )


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_admin), Depends(csrf_protect)],
)
def delete_user(user_id: int, service: UserService = Depends(get_user_service)) -> MessageResponse:
    service.delete_user(user_id)
    return MessageResponse(message=f"User {user_id} deleted successfully")
