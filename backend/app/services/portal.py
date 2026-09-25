import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.slugify import slugify
from app.db.models.citizen import Citizen
from app.db.models.portal import Portal, PortalUserRole
from app.db.models.portal_request import Request, RequestFieldValue, RequestType, RequestTypeField
from app.db.models.rbac import OrgRole
from app.db.models.user import OrgUser
from app.schemas.portal import (
    AssignPortalUserRequest,
    PortalCreate,
    PortalOut,
    PortalUpdate,
    RequestFieldValueOut,
    RequestTypeCreate,
    RequestTypeFieldCreate,
    RequestTypeFieldOut,
    RequestTypeFieldUpdate,
    RequestTypeOut,
    RequestTypeUpdate,
    RequestOut,
    RequestUpdate,
    VALID_FIELD_TYPES,
)
from app.services.rbac import PORTAL_PERMISSIONS


async def _get_portal(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID) -> Portal:
    result = await db.execute(
        select(Portal).where(Portal.id == portal_id, Portal.org_id == org_id)
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


# --- Portal Users ---

async def assign_portal_user(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, data: AssignPortalUserRequest) -> None:
    await _get_portal(db, org_id, portal_id)

    user = (await db.execute(select(OrgUser).where(OrgUser.id == data.user_id, OrgUser.org_id == org_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    role = (await db.execute(
        select(OrgRole).where(OrgRole.id == data.role_id, OrgRole.org_id == org_id, OrgRole.level == "portal")
    )).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portal role not found")

    existing = (await db.execute(
        select(PortalUserRole).where(PortalUserRole.portal_id == portal_id, PortalUserRole.user_id == data.user_id)
    )).scalar_one_or_none()
    if existing:
        existing.role_id = data.role_id
    else:
        db.add(PortalUserRole(portal_id=portal_id, user_id=data.user_id, role_id=data.role_id))

    await db.commit()


async def remove_portal_user(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, user_id: uuid.UUID) -> None:
    await _get_portal(db, org_id, portal_id)
    existing = (await db.execute(
        select(PortalUserRole).where(PortalUserRole.portal_id == portal_id, PortalUserRole.user_id == user_id)
    )).scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not assigned to this portal")
    await db.delete(existing)
    await db.commit()


# --- Helpers ---

async def _load_request_type(db: AsyncSession, portal_id: uuid.UUID, rt_id: uuid.UUID) -> RequestType:
    from sqlalchemy.orm import selectinload
    rt = (await db.execute(
        select(RequestType)
        .where(RequestType.id == rt_id, RequestType.portal_id == portal_id)
        .options(selectinload(RequestType.fields))
    )).scalar_one_or_none()
    if not rt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request type not found")
    return rt


async def _load_request(db: AsyncSession, portal_id: uuid.UUID, request_id: uuid.UUID) -> Request:
    from sqlalchemy.orm import selectinload
    req = (await db.execute(
        select(Request)
        .where(Request.id == request_id, Request.portal_id == portal_id)
        .options(
            selectinload(Request.request_type),
            selectinload(Request.field_values).selectinload(RequestFieldValue.field),
        )
    )).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return req


def _request_to_out(req: Request) -> RequestOut:
    field_values = [
        RequestFieldValueOut(
            field_id=fv.field_id,
            label=fv.field.label,
            field_type=fv.field.field_type,
            value=fv.value,
        )
        for fv in sorted(req.field_values, key=lambda fv: fv.field.order)
    ]
    return RequestOut(
        id=req.id,
        portal_id=req.portal_id,
        request_type_id=req.request_type_id,
        request_type_name=req.request_type.name if req.request_type else None,
        citizen_id=req.citizen_id,
        title=req.title,
        status=req.status,
        field_values=field_values,
        created_at=req.created_at,
    )


# --- Request Types ---

async def list_request_types(db: AsyncSession, portal_id: uuid.UUID) -> list[RequestTypeOut]:
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(RequestType)
        .where(RequestType.portal_id == portal_id)
        .options(selectinload(RequestType.fields))
        .order_by(RequestType.created_at)
    )
    return [RequestTypeOut.model_validate(rt) for rt in result.scalars().all()]


async def create_request_type(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, data: RequestTypeCreate) -> RequestTypeOut:
    await _get_portal(db, org_id, portal_id)
    rt = RequestType(portal_id=portal_id, name=data.name, description=data.description)
    db.add(rt)
    await db.commit()
    rt = await _load_request_type(db, portal_id, rt.id)
    return RequestTypeOut.model_validate(rt)


async def update_request_type(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, rt_id: uuid.UUID, data: RequestTypeUpdate) -> RequestTypeOut:
    await _get_portal(db, org_id, portal_id)
    rt = await _load_request_type(db, portal_id, rt_id)
    if data.name is not None:
        rt.name = data.name
    if data.description is not None:
        rt.description = data.description
    await db.commit()
    rt = await _load_request_type(db, portal_id, rt_id)
    return RequestTypeOut.model_validate(rt)


async def delete_request_type(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, rt_id: uuid.UUID) -> None:
    await _get_portal(db, org_id, portal_id)
    rt = await _load_request_type(db, portal_id, rt_id)
    await db.delete(rt)
    await db.commit()


# --- Request Type Fields ---

async def list_request_type_fields(db: AsyncSession, portal_id: uuid.UUID, rt_id: uuid.UUID) -> list[RequestTypeFieldOut]:
    rt = await _load_request_type(db, portal_id, rt_id)
    return [RequestTypeFieldOut.model_validate(f) for f in rt.fields]


async def create_request_type_field(
    db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, rt_id: uuid.UUID, data: RequestTypeFieldCreate
) -> RequestTypeFieldOut:
    await _get_portal(db, org_id, portal_id)
    if data.field_type not in VALID_FIELD_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid field_type. Must be one of: {', '.join(VALID_FIELD_TYPES)}")
    if data.field_type == "select" and not data.options:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Select fields require at least one option")
    if data.field_type != "select" and data.options:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Options are only valid for select fields")

    await _load_request_type(db, portal_id, rt_id)
    field = RequestTypeField(
        request_type_id=rt_id,
        label=data.label,
        field_type=data.field_type,
        required=data.required,
        order=data.order,
        options=data.options,
    )
    db.add(field)
    await db.commit()
    await db.refresh(field)
    return RequestTypeFieldOut.model_validate(field)


async def update_request_type_field(
    db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, rt_id: uuid.UUID, field_id: uuid.UUID, data: RequestTypeFieldUpdate
) -> RequestTypeFieldOut:
    await _get_portal(db, org_id, portal_id)
    await _load_request_type(db, portal_id, rt_id)
    field = (await db.execute(
        select(RequestTypeField).where(RequestTypeField.id == field_id, RequestTypeField.request_type_id == rt_id)
    )).scalar_one_or_none()
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")

    if data.field_type is not None:
        if data.field_type not in VALID_FIELD_TYPES:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid field_type. Must be one of: {', '.join(VALID_FIELD_TYPES)}")
        field.field_type = data.field_type
    if data.label is not None:
        field.label = data.label
    if data.required is not None:
        field.required = data.required
    if data.order is not None:
        field.order = data.order
    if data.options is not None:
        field.options = data.options

    await db.commit()
    await db.refresh(field)
    return RequestTypeFieldOut.model_validate(field)


async def delete_request_type_field(
    db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, rt_id: uuid.UUID, field_id: uuid.UUID
) -> None:
    await _get_portal(db, org_id, portal_id)
    await _load_request_type(db, portal_id, rt_id)
    field = (await db.execute(
        select(RequestTypeField).where(RequestTypeField.id == field_id, RequestTypeField.request_type_id == rt_id)
    )).scalar_one_or_none()
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")
    await db.delete(field)
    await db.commit()


# --- Portal Requests (admin view) ---

async def list_portal_requests(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID) -> list[RequestOut]:
    from sqlalchemy.orm import selectinload
    await _get_portal(db, org_id, portal_id)
    result = await db.execute(
        select(Request)
        .where(Request.portal_id == portal_id)
        .options(
            selectinload(Request.request_type),
            selectinload(Request.field_values).selectinload(RequestFieldValue.field),
        )
        .order_by(Request.created_at.desc())
    )
    return [_request_to_out(r) for r in result.scalars().all()]


async def update_portal_request(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, request_id: uuid.UUID, data: RequestUpdate) -> RequestOut:
    await _get_portal(db, org_id, portal_id)
    req = await _load_request(db, portal_id, request_id)
    if data.status is not None:
        req.status = data.status
    if data.title is not None:
        req.title = data.title
    await db.commit()
    req = await _load_request(db, portal_id, request_id)
    return _request_to_out(req)
