from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_permissions
from app.db.models.user import OrgUser
from app.schemas.rbac import RoleCreate, RoleOut, RoleUpdate
from app.services import rbac as rbac_service

router = APIRouter(prefix="/org/roles", tags=["Org Roles"])

_401 = {401: {"description": "Missing or invalid authentication token"}}
_403 = {403: {"description": "Requires `org.users.manage` permission"}}
_404 = {404: {"description": "Role not found"}}


@router.get(
    "",
    response_model=list[RoleOut],
    summary="List roles",
    description="Returns all roles defined in the organization, including both org-level and portal-level roles.",
    responses={**_401},
)
async def list_roles(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await rbac_service.list_roles(db, current_user.org_id)


@router.post(
    "",
    response_model=RoleOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a role",
    description="Creates a new role with a set of permissions. Set `level` to `'portal'` for roles that will be "
                "assigned at the portal level — portal-level roles only accept portal permission keys. "
                "Requires `org.users.manage`.",
    responses={**_401, **_403, 422: {"description": "Invalid permission keys or level mismatch"}},
)
async def create_role(
    data: RoleCreate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await rbac_service.create_role(db, current_user.org_id, data)


@router.get(
    "/{role_id}",
    response_model=RoleOut,
    summary="Get a role",
    description="Returns a single role by ID.",
    responses={**_401, **_404},
)
async def get_role(
    role_id: UUID,
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await rbac_service.get_role(db, current_user.org_id, role_id)


@router.patch(
    "/{role_id}",
    response_model=RoleOut,
    summary="Update a role",
    description="Updates a role's name, description, or permissions. The `permissions` field **replaces** the "
                "full permission set — send the complete list you want, not a diff. "
                "Requires `org.users.manage`.",
    responses={**_401, **_403, **_404, 422: {"description": "Invalid permission keys or level mismatch"}},
)
async def update_role(
    role_id: UUID,
    data: RoleUpdate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await rbac_service.update_role(db, current_user.org_id, role_id, data)


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a role",
    description="Deletes a role and removes all assignments of that role from users and portals. "
                "Requires `org.users.manage`.",
    responses={**_401, **_403, **_404},
)
async def delete_role(
    role_id: UUID,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await rbac_service.delete_role(db, current_user.org_id, role_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
