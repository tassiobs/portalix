from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_permissions
from app.db.models.user import OrgUser
from app.schemas.org import OrgOut, OrgUpdate
from app.services import org as org_service

router = APIRouter(prefix="/org", tags=["Org"])


@router.get("", response_model=OrgOut)
async def get_org(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await org_service.get_org(db, current_user.org_id)


@router.patch("", response_model=OrgOut)
async def update_org(
    data: OrgUpdate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await org_service.update_org(db, current_user.org_id, data)
