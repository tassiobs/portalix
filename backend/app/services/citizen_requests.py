import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.citizen import Citizen
from app.db.models.portal_request import Request, RequestFieldValue, RequestType, RequestTypeField
from app.schemas.citizen import CitizenRequestCreate, CitizenRequestOut
from app.schemas.portal import RequestFieldValueOut, RequestTypeOut


def _request_to_out(req: Request) -> CitizenRequestOut:
    field_values = [
        RequestFieldValueOut(
            field_id=fv.field_id,
            label=fv.field.label,
            field_type=fv.field.field_type,
            value=fv.value,
        )
        for fv in sorted(req.field_values, key=lambda fv: fv.field.order)
    ]
    return CitizenRequestOut(
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


async def list_request_types(db: AsyncSession, portal_id: uuid.UUID) -> list[RequestTypeOut]:
    result = await db.execute(
        select(RequestType)
        .where(RequestType.portal_id == portal_id)
        .options(selectinload(RequestType.fields))
        .order_by(RequestType.name)
    )
    return [RequestTypeOut.model_validate(rt) for rt in result.scalars().all()]


async def list_citizen_requests(db: AsyncSession, citizen_id: uuid.UUID, portal_id: uuid.UUID) -> list[CitizenRequestOut]:
    result = await db.execute(
        select(Request)
        .where(Request.citizen_id == citizen_id, Request.portal_id == portal_id)
        .options(
            selectinload(Request.request_type),
            selectinload(Request.field_values).selectinload(RequestFieldValue.field),
        )
        .order_by(Request.created_at.desc())
    )
    return [_request_to_out(r) for r in result.scalars().all()]


async def create_request(db: AsyncSession, citizen: Citizen, data: CitizenRequestCreate) -> CitizenRequestOut:
    rt = (await db.execute(
        select(RequestType)
        .where(RequestType.id == data.request_type_id, RequestType.portal_id == citizen.portal_id)
        .options(selectinload(RequestType.fields))
    )).scalar_one_or_none()
    if not rt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request type not found")

    # Validate required fields
    submitted_ids = {fv.field_id for fv in data.field_values}
    for field in rt.fields:
        if field.required and field.id not in submitted_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Required field missing: {field.label}",
            )

    # Validate submitted field IDs belong to this request type
    valid_ids = {f.id for f in rt.fields}
    for fv in data.field_values:
        if fv.field_id not in valid_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown field: {fv.field_id}",
            )

    req = Request(
        portal_id=citizen.portal_id,
        request_type_id=data.request_type_id,
        citizen_id=citizen.id,
        title=data.title,
    )
    db.add(req)
    await db.flush()

    for fv in data.field_values:
        db.add(RequestFieldValue(request_id=req.id, field_id=fv.field_id, value=fv.value))

    await db.commit()

    result = await db.execute(
        select(Request)
        .where(Request.id == req.id)
        .options(
            selectinload(Request.request_type),
            selectinload(Request.field_values).selectinload(RequestFieldValue.field),
        )
    )
    req = result.scalar_one()
    return _request_to_out(req)


async def get_request(db: AsyncSession, citizen: Citizen, request_id: str) -> CitizenRequestOut:
    req = (await db.execute(
        select(Request)
        .where(Request.id == uuid.UUID(request_id), Request.citizen_id == citizen.id)
        .options(
            selectinload(Request.request_type),
            selectinload(Request.field_values).selectinload(RequestFieldValue.field),
        )
    )).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return _request_to_out(req)
