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


@router.get("", response_model=OrgUserPage)
async def list_users(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    return await user_service.list_users(db, current_user.org_id, page, per_page)


@router.post("", response_model=OrgUserCreateResponse, status_code=201)
async def create_user(
    data: OrgUserCreate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await user_service.create_user(db, current_user.org_id, data, current_user)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: UUID,
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await user_service.get_user(db, current_user.org_id, user_id)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: UUID,
    data: OrgUserUpdate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await user_service.update_user(db, current_user.org_id, user_id, data)


@router.post("/{user_id}/deactivate", status_code=204)
async def deactivate_user(
    user_id: UUID,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await user_service.deactivate_user(db, current_user.org_id, user_id)


@router.get("/{user_id}/roles", response_model=list[RoleOut])
async def list_user_roles(
    user_id: UUID,
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await rbac_service.list_user_roles(db, user_id)


@router.post("/{user_id}/roles", status_code=204)
async def assign_role(
    user_id: UUID,
    data: AssignRoleRequest,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await rbac_service.assign_role(db, current_user.org_id, user_id, data.role_id)


@router.delete("/{user_id}/roles/{role_id}", status_code=204)
async def remove_role(
    user_id: UUID,
    role_id: UUID,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await rbac_service.remove_role(db, user_id, role_id)
