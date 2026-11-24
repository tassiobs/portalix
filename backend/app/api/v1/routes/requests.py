from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_permissions
from app.db.models.request import OrgRequest
from app.db.models.user import OrgUser
from app.schemas.request import OrgRequestCreate, OrgRequestOut, OrgRequestUpdate

router = APIRouter(prefix="/org/requests", tags=["Requests"])

_401 = {401: {"description": "Missing or invalid authentication token"}}
_403 = {403: {"description": "Insufficient permissions"}}
_404 = {404: {"description": "Request not found"}}


@router.get(
    "",
    response_model=list[OrgRequestOut],
    summary="List org requests",
    description="Returns all requests in the organization. Requires `requests:read`.",
    responses={**_401, **_403},
)
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


@router.post(
    "",
    response_model=OrgRequestOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a request",
    description="Creates a new org-level request. Requires `requests:create`.",
    responses={**_401, **_403},
)
async def create_request(
    data: OrgRequestCreate,
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


@router.patch(
    "/{request_id}",
    response_model=OrgRequestOut,
    summary="Update a request",
    description="Updates a request's title or status. Requires `requests:update`.",
    responses={**_401, **_403, **_404},
)
async def update_request(
    request_id: UUID,
    data: OrgRequestUpdate,
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


@router.delete(
    "/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a request",
    description="Permanently deletes a request. Requires `requests:delete`.",
    responses={**_401, **_403, **_404},
)
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
