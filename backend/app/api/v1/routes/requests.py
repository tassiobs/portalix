from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_permissions
from app.db.models.request import OrgRequest
from app.db.models.user import OrgUser
from app.schemas.request import RequestCreate, RequestOut, RequestUpdate

router = APIRouter(prefix="/org/requests", tags=["Requests"])


@router.get("", response_model=list[RequestOut])
async def list_requests(
    current_user: Annotated[OrgUser, Depends(require_permissions("requests:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(OrgRequest)
        .where(OrgRequest.org_id == current_user.org_id)
        .order_by(OrgRequest.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=RequestOut, status_code=status.HTTP_201_CREATED)
async def create_request(
    data: RequestCreate,
    current_user: Annotated[OrgUser, Depends(require_permissions("requests:create"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    req = OrgRequest(
        org_id=current_user.org_id,
        created_by_id=current_user.id,
        title=data.title,
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return req


@router.patch("/{request_id}", response_model=RequestOut)
async def update_request(
    request_id: UUID,
    data: RequestUpdate,
    current_user: Annotated[OrgUser, Depends(require_permissions("requests:update"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(OrgRequest).where(
            OrgRequest.id == request_id,
            OrgRequest.org_id == current_user.org_id,
        )
    )
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if data.title is not None:
        req.title = data.title
    if data.status is not None:
        req.status = data.status

    await db.commit()
    await db.refresh(req)
    return req


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_request(
    request_id: UUID,
    current_user: Annotated[OrgUser, Depends(require_permissions("requests:delete"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(OrgRequest).where(
            OrgRequest.id == request_id,
            OrgRequest.org_id == current_user.org_id,
        )
    )
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    await db.delete(req)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
