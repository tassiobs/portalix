from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_permissions
from app.db.models.user import OrgUser
from app.schemas.org import OrgSettingsOut, OrgSettingsUpdate
from app.services import org as org_service

router = APIRouter(prefix="/org/settings", tags=["Org Settings"])

_401 = {401: {"description": "Missing or invalid authentication token"}}
_403 = {403: {"description": "Requires `org.users.manage` permission"}}


@router.get(
    "",
    response_model=OrgSettingsOut,
    summary="Get org security settings",
    description="Returns the organization's security configuration including lockout policy, MFA settings, "
                "and customer identity scope.",
    responses={**_401},
)
async def get_org_settings(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await org_service.get_org_settings(db, current_user.org_id)


@router.patch(
    "",
    response_model=OrgSettingsOut,
    summary="Update org security settings",
    description="Updates one or more security settings. All fields are optional — only provided fields are changed. "
                "Requires `org.users.manage`.",
    responses={**_401, **_403},
)
async def update_org_settings(
    data: OrgSettingsUpdate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await org_service.update_org_settings(db, current_user.org_id, data, current_user)
