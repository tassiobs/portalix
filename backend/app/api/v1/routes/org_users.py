from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_permissions
from app.db.models.user import OrgUser
from app.schemas.rbac import AssignRoleRequest, RoleOut
from app.schemas.user import OrgUserCreate, OrgUserCreateResponse, OrgUserPage, OrgUserUpdate, UserOut
from app.services import rbac as rbac_service
from app.services import user as user_service

router = APIRouter(prefix="/org/users", tags=["Org Users"])

_401 = {401: {"description": "Missing or invalid authentication token"}}
_403 = {403: {"description": "Requires `org.users.manage` permission"}}
_404 = {404: {"description": "User not found"}}
_409 = {409: {"description": "Email address already registered in this org"}}


@router.get(
    "",
    response_model=OrgUserPage,
    summary="List org users",
    description="Returns a paginated list of all users in the organization.",
    responses={**_401},
)
async def list_users(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
):
    return await user_service.list_users(db, current_user.org_id, page, per_page)


@router.post(
    "",
    response_model=OrgUserCreateResponse,
    status_code=201,
    summary="Invite a new user",
    description="Creates a user account and sends them an invitation email with a link to set their password. "
                "Requires `org.users.manage`.",
    responses={**_401, **_403, **_409},
)
async def create_user(
    data: OrgUserCreate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await user_service.create_user(db, current_user.org_id, data, current_user)


@router.get(
    "/{user_id}",
    response_model=UserOut,
    summary="Get a user",
    description="Returns the profile of a specific org user including their role assignments.",
    responses={**_401, **_404},
)
async def get_user(
    user_id: UUID,
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await user_service.get_user(db, current_user.org_id, user_id)


@router.patch(
    "/{user_id}",
    response_model=UserOut,
    summary="Update a user",
    description="Updates a user's name or status. Set `status` to `'inactive'` to disable their access. "
                "Requires `org.users.manage`.",
    responses={**_401, **_403, **_404},
)
async def update_user(
    user_id: UUID,
    data: OrgUserUpdate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await user_service.update_user(db, current_user.org_id, user_id, data)


@router.post(
    "/{user_id}/deactivate",
    status_code=204,
    summary="Deactivate a user",
    description="Sets the user's status to `inactive`, immediately blocking their access. "
                "Requires `org.users.manage`.",
    responses={**_401, **_403, **_404},
)
async def deactivate_user(
    user_id: UUID,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await user_service.deactivate_user(db, current_user.org_id, user_id)


@router.get(
    "/{user_id}/roles",
    response_model=list[RoleOut],
    summary="List user roles",
    description="Returns all roles assigned to the user across the org and all portals.",
    responses={**_401, **_404},
)
async def list_user_roles(
    user_id: UUID,
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await rbac_service.list_user_roles(db, user_id)


@router.post(
    "/{user_id}/roles",
    status_code=204,
    summary="Assign a role to a user",
    description="Assigns an org-level role to the user. Use `POST /org/portals/{portal_id}/users` to assign portal-scoped roles. "
                "Requires `org.users.manage`.",
    responses={**_401, **_403, **_404, 409: {"description": "Role already assigned to this user"}},
)
async def assign_role(
    user_id: UUID,
    data: AssignRoleRequest,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await rbac_service.assign_role(db, current_user.org_id, user_id, data.role_id)


@router.delete(
    "/{user_id}/roles/{role_id}",
    status_code=204,
    summary="Remove a role from a user",
    description="Removes an org-level role assignment from a user. Requires `org.users.manage`.",
    responses={**_401, **_403, **_404},
)
async def remove_role(
    user_id: UUID,
    role_id: UUID,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await rbac_service.remove_role(db, user_id, role_id)
