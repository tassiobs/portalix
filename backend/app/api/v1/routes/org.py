from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_permissions
from app.db.models.user import OrgUser
from app.schemas.org import OrgOut, OrgUpdate
from app.services import org as org_service

router = APIRouter(prefix="/org", tags=["Org"])

_401 = {401: {"description": "Missing or invalid authentication token"}}
_403 = {403: {"description": "Requires `org.users.manage` permission"}}


@router.get(
    "",
    response_model=OrgOut,
    summary="Get organization",
    description="Returns the organization the authenticated user belongs to.",
    responses={**_401},
)
async def get_org(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await org_service.get_org(db, current_user.org_id)


@router.patch(
    "",
    response_model=OrgOut,
    summary="Update organization",
    description="Updates the organization's name or slug. Requires `org.users.manage`. "
                "Changing the slug will break existing portal URLs — use with caution.",
    responses={**_401, **_403},
)
async def update_org(
    data: OrgUpdate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await org_service.update_org(db, current_user.org_id, data)
