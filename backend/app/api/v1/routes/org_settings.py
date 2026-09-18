from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_permissions
from app.db.models.user import OrgUser
from app.schemas.org import OrgSettingsOut, OrgSettingsUpdate
from app.services import org as org_service

router = APIRouter(prefix="/org/settings", tags=["Org Settings"])


@router.get("", response_model=OrgSettingsOut)
async def get_org_settings(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await org_service.get_org_settings(db, current_user.org_id)


@router.patch("", response_model=OrgSettingsOut)
async def update_org_settings(
    data: OrgSettingsUpdate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await org_service.update_org_settings(db, current_user.org_id, data, current_user)
