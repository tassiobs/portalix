from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_permissions
from app.db.models.user import OrgUser
from app.schemas.rbac import RoleCreate, RoleOut, RoleUpdate
from app.services import rbac as rbac_service

router = APIRouter(prefix="/org/roles", tags=["Org Roles"])


@router.get("", response_model=list[RoleOut])
async def list_roles(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await rbac_service.list_roles(db, current_user.org_id)


@router.post("", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
async def create_role(
    data: RoleCreate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await rbac_service.create_role(db, current_user.org_id, data)


@router.get("/{role_id}", response_model=RoleOut)
async def get_role(
    role_id: UUID,
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await rbac_service.get_role(db, current_user.org_id, role_id)


@router.patch("/{role_id}", response_model=RoleOut)
async def update_role(
    role_id: UUID,
    data: RoleUpdate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await rbac_service.update_role(db, current_user.org_id, role_id, data)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await rbac_service.delete_role(db, current_user.org_id, role_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
