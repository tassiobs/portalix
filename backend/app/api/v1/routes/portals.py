import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_permissions
from app.db.models.user import OrgUser
from app.schemas.portal import (
    AssignPortalUserRequest,
    PortalCreate,
    PortalOut,
    PortalRoleCreate,
    PortalRoleOut,
    PortalRoleUpdate,
    PortalUpdate,
    RequestTypeCreate,
    RequestTypeOut,
    RequestTypeUpdate,
    RequestOut,
    RequestUpdate,
)
from app.services import portal as portal_service
from app.services.portal import PORTAL_PERMISSIONS

router = APIRouter(prefix="/org/portals", tags=["portals"])


@router.get("/permissions")
async def list_portal_permissions(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
):
    return {"data": PORTAL_PERMISSIONS}


@router.get("", response_model=list[PortalOut])
async def list_portals(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.list_portals(db, current_user.org_id)


@router.post("", response_model=PortalOut, status_code=status.HTTP_201_CREATED)
async def create_portal(
    data: PortalCreate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.create_portal(db, current_user.org_id, data, current_user)


@router.patch("/{portal_id}", response_model=PortalOut)
async def update_portal(
    portal_id: uuid.UUID,
    data: PortalUpdate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.update_portal(db, current_user.org_id, portal_id, data)


@router.delete("/{portal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portal(
    portal_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await portal_service.delete_portal(db, current_user.org_id, portal_id)


# --- Portal Roles ---

@router.get("/{portal_id}/roles", response_model=list[PortalRoleOut])
async def list_portal_roles(
    portal_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.list_portal_roles(db, current_user.org_id, portal_id)


@router.post("/{portal_id}/roles", response_model=PortalRoleOut, status_code=status.HTTP_201_CREATED)
async def create_portal_role(
    portal_id: uuid.UUID,
    data: PortalRoleCreate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.create_portal_role(db, current_user.org_id, portal_id, data)


@router.patch("/{portal_id}/roles/{role_id}", response_model=PortalRoleOut)
async def update_portal_role(
    portal_id: uuid.UUID,
    role_id: uuid.UUID,
    data: PortalRoleUpdate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.update_portal_role(db, current_user.org_id, portal_id, role_id, data)


@router.delete("/{portal_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portal_role(
    portal_id: uuid.UUID,
    role_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await portal_service.delete_portal_role(db, current_user.org_id, portal_id, role_id)


# --- Portal Users ---

@router.post("/{portal_id}/users", status_code=status.HTTP_204_NO_CONTENT)
async def assign_portal_user(
    portal_id: uuid.UUID,
    data: AssignPortalUserRequest,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await portal_service.assign_portal_user(db, current_user.org_id, portal_id, data)


@router.delete("/{portal_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_portal_user(
    portal_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await portal_service.remove_portal_user(db, current_user.org_id, portal_id, user_id)


# --- Request Types ---

@router.get("/{portal_id}/request-types", response_model=list[RequestTypeOut])
async def list_request_types(
    portal_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.list_request_types(db, portal_id)


@router.post("/{portal_id}/request-types", response_model=RequestTypeOut, status_code=status.HTTP_201_CREATED)
async def create_request_type(
    portal_id: uuid.UUID,
    data: RequestTypeCreate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.create_request_type(db, current_user.org_id, portal_id, data)


@router.patch("/{portal_id}/request-types/{rt_id}", response_model=RequestTypeOut)
async def update_request_type(
    portal_id: uuid.UUID,
    rt_id: uuid.UUID,
    data: RequestTypeUpdate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.update_request_type(db, current_user.org_id, portal_id, rt_id, data)


@router.delete("/{portal_id}/request-types/{rt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_request_type(
    portal_id: uuid.UUID,
    rt_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await portal_service.delete_request_type(db, current_user.org_id, portal_id, rt_id)


# --- Portal Requests (admin view) ---

@router.get("/{portal_id}/requests", response_model=list[RequestOut])
async def list_portal_requests(
    portal_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.list_portal_requests(db, current_user.org_id, portal_id)


@router.patch("/{portal_id}/requests/{request_id}", response_model=RequestOut)
async def update_portal_request(
    portal_id: uuid.UUID,
    request_id: uuid.UUID,
    data: RequestUpdate,
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.update_portal_request(db, current_user.org_id, portal_id, request_id, data)
