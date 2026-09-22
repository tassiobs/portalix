import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.slugify import slugify
from app.db.models.citizen import Citizen
from app.db.models.portal import Portal, PortalRole, PortalRolePermission, PortalUserRole
from app.db.models.portal_request import Request, RequestType
from app.db.models.user import OrgUser
from app.schemas.portal import (
    AssignPortalUserRequest,
    PortalCreate,
    PortalOut,
    PortalRoleCreate,
    PortalRoleOut,
    PortalUpdate,
    RequestTypeCreate,
    RequestTypeOut,
    RequestTypeUpdate,
    RequestOut,
    RequestUpdate,
    PortalRoleUpdate,
)


PORTAL_PERMISSIONS = [
    {
        "key": "portal.requests:read",
        "label": "View Requests",
        "description": "View requests submitted on this portal",
        "level": "portal",
    },
    {
        "key": "portal.requests:update",
        "label": "Update Requests",
        "description": "Update status or title of requests on this portal",
        "level": "portal",
    },
    {
        "key": "portal.request_types:manage",
        "label": "Manage Request Types",
        "description": "Create, update, and delete request types on this portal",
        "level": "portal",
    },
    {
        "key": "portal.users:manage",
        "label": "Manage Portal Users",
        "description": "Add/remove users and assign portal roles",
        "level": "portal",
    },
    {
        "key": "portal.settings:manage",
        "label": "Manage Portal Settings",
        "description": "Update portal name, description, and domain",
        "level": "portal",
    },
]

PORTAL_SUPER_ADMIN_PERMISSIONS = [
    "portal.requests:read",
    "portal.requests:update",
    "portal.request_types:manage",
    "portal.users:manage",
    "portal.settings:manage",
]


def _build_portal_role_out(role: PortalRole) -> PortalRoleOut:
    return PortalRoleOut(
        id=role.id,
        portal_id=role.portal_id,
        name=role.name,
        description=role.description,
        permissions=[p.permission for p in role.permissions],
        is_default=role.is_default,
        level="portal",
        created_at=role.created_at,
    )


async def _get_portal(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID) -> Portal:
    result = await db.execute(
        select(Portal)
        .where(Portal.id == portal_id, Portal.org_id == org_id)
        .options(selectinload(Portal.roles).selectinload(PortalRole.permissions))
    )
    portal = result.scalar_one_or_none()
    if not portal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portal not found")
    return portal


# --- Portals ---

async def list_portals(db: AsyncSession, org_id: uuid.UUID) -> list[PortalOut]:
    result = await db.execute(select(Portal).where(Portal.org_id == org_id).order_by(Portal.created_at))
    return [PortalOut.model_validate(p) for p in result.scalars().all()]


async def create_portal(db: AsyncSession, org_id: uuid.UUID, data: PortalCreate, created_by: OrgUser) -> PortalOut:
    base_slug = slugify(data.name)
    slug = base_slug
    suffix = 1
    while (await db.execute(select(Portal).where(Portal.org_id == org_id, Portal.slug == slug))).scalar_one_or_none():
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    if data.domain:
        existing = (await db.execute(select(Portal).where(Portal.domain == data.domain))).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Domain already in use")

    portal = Portal(
        org_id=org_id,
        name=data.name,
        slug=slug,
        description=data.description,
        domain=data.domain,
        created_by_id=created_by.id,
    )
    db.add(portal)
    await db.flush()

    # Seed Portal Super Admin role
    super_admin_role = PortalRole(portal_id=portal.id, name="Portal Super Admin", is_default=True)
    db.add(super_admin_role)
    await db.flush()

    for perm in PORTAL_SUPER_ADMIN_PERMISSIONS:
        db.add(PortalRolePermission(role_id=super_admin_role.id, permission=perm))

    await db.commit()
    await db.refresh(portal)
    return PortalOut.model_validate(portal)


async def update_portal(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, data: PortalUpdate) -> PortalOut:
    portal = await _get_portal(db, org_id, portal_id)

    if data.name is not None:
        portal.name = data.name
    if data.description is not None:
        portal.description = data.description
    if data.domain is not None:
        existing = (await db.execute(select(Portal).where(Portal.domain == data.domain, Portal.id != portal_id))).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Domain already in use")
        portal.domain = data.domain

    await db.commit()
    await db.refresh(portal)
    return PortalOut.model_validate(portal)


async def delete_portal(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID) -> None:
    portal = await _get_portal(db, org_id, portal_id)
    await db.delete(portal)
    await db.commit()


# --- Portal Roles ---

async def list_portal_roles(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID) -> list[PortalRoleOut]:
    await _get_portal(db, org_id, portal_id)
    result = await db.execute(
        select(PortalRole)
        .where(PortalRole.portal_id == portal_id)
        .options(selectinload(PortalRole.permissions))
        .order_by(PortalRole.created_at)
    )
    return [_build_portal_role_out(r) for r in result.scalars().all()]


async def create_portal_role(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, data: PortalRoleCreate) -> PortalRoleOut:
    await _get_portal(db, org_id, portal_id)
    role = PortalRole(portal_id=portal_id, name=data.name, description=data.description)
    db.add(role)
    await db.flush()
    for perm in data.permissions:
        db.add(PortalRolePermission(role_id=role.id, permission=perm))
    await db.commit()
    result = await db.execute(
        select(PortalRole).where(PortalRole.id == role.id).options(selectinload(PortalRole.permissions))
    )
    return _build_portal_role_out(result.scalar_one())


async def update_portal_role(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, role_id: uuid.UUID, data: PortalRoleUpdate) -> PortalRoleOut:
    await _get_portal(db, org_id, portal_id)
    result = await db.execute(
        select(PortalRole).where(PortalRole.id == role_id, PortalRole.portal_id == portal_id).options(selectinload(PortalRole.permissions))
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    if data.name is not None:
        role.name = data.name
    if data.description is not None:
        role.description = data.description
    if data.permissions is not None:
        for p in list(role.permissions):
            await db.delete(p)
        await db.flush()
        for perm in data.permissions:
            db.add(PortalRolePermission(role_id=role.id, permission=perm))

    await db.commit()
    result = await db.execute(
        select(PortalRole).where(PortalRole.id == role_id).options(selectinload(PortalRole.permissions))
    )
    return _build_portal_role_out(result.scalar_one())


async def delete_portal_role(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, role_id: uuid.UUID) -> None:
    await _get_portal(db, org_id, portal_id)
    result = await db.execute(select(PortalRole).where(PortalRole.id == role_id, PortalRole.portal_id == portal_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role.is_default:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot delete a default role")
    await db.delete(role)
    await db.commit()


# --- Portal Users ---

async def assign_portal_user(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, data: AssignPortalUserRequest) -> None:
    await _get_portal(db, org_id, portal_id)

    user = (await db.execute(select(OrgUser).where(OrgUser.id == data.user_id, OrgUser.org_id == org_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    role = (await db.execute(select(PortalRole).where(PortalRole.id == data.role_id, PortalRole.portal_id == portal_id))).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    existing = (await db.execute(select(PortalUserRole).where(PortalUserRole.portal_id == portal_id, PortalUserRole.user_id == data.user_id))).scalar_one_or_none()
    if existing:
        existing.role_id = data.role_id
    else:
        db.add(PortalUserRole(portal_id=portal_id, user_id=data.user_id, role_id=data.role_id))

    await db.commit()


async def remove_portal_user(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, user_id: uuid.UUID) -> None:
    await _get_portal(db, org_id, portal_id)
    existing = (await db.execute(select(PortalUserRole).where(PortalUserRole.portal_id == portal_id, PortalUserRole.user_id == user_id))).scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not assigned to this portal")
    await db.delete(existing)
    await db.commit()


# --- Request Types ---

async def list_request_types(db: AsyncSession, portal_id: uuid.UUID) -> list[RequestTypeOut]:
    result = await db.execute(select(RequestType).where(RequestType.portal_id == portal_id).order_by(RequestType.created_at))
    return [RequestTypeOut.model_validate(rt) for rt in result.scalars().all()]


async def create_request_type(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, data: RequestTypeCreate) -> RequestTypeOut:
    await _get_portal(db, org_id, portal_id)
    rt = RequestType(portal_id=portal_id, name=data.name, description=data.description)
    db.add(rt)
    await db.commit()
    await db.refresh(rt)
    return RequestTypeOut.model_validate(rt)


async def update_request_type(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, rt_id: uuid.UUID, data: RequestTypeUpdate) -> RequestTypeOut:
    await _get_portal(db, org_id, portal_id)
    rt = (await db.execute(select(RequestType).where(RequestType.id == rt_id, RequestType.portal_id == portal_id))).scalar_one_or_none()
    if not rt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request type not found")
    if data.name is not None:
        rt.name = data.name
    if data.description is not None:
        rt.description = data.description
    await db.commit()
    await db.refresh(rt)
    return RequestTypeOut.model_validate(rt)


async def delete_request_type(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, rt_id: uuid.UUID) -> None:
    await _get_portal(db, org_id, portal_id)
    rt = (await db.execute(select(RequestType).where(RequestType.id == rt_id, RequestType.portal_id == portal_id))).scalar_one_or_none()
    if not rt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request type not found")
    await db.delete(rt)
    await db.commit()


# --- Portal Requests (admin view) ---

async def list_portal_requests(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID) -> list[RequestOut]:
    await _get_portal(db, org_id, portal_id)
    result = await db.execute(select(Request).where(Request.portal_id == portal_id).order_by(Request.created_at.desc()))
    return [RequestOut.model_validate(r) for r in result.scalars().all()]


async def update_portal_request(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, request_id: uuid.UUID, data: RequestUpdate) -> RequestOut:
    await _get_portal(db, org_id, portal_id)
    req = (await db.execute(select(Request).where(Request.id == request_id, Request.portal_id == portal_id))).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if data.status is not None:
        req.status = data.status
    if data.title is not None:
        req.title = data.title
    await db.commit()
    await db.refresh(req)
    return RequestOut.model_validate(req)
