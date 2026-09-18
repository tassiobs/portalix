from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_active_user
from app.db.models.user import OrgUser
from app.services.rbac import ORG_PERMISSIONS

router = APIRouter(prefix="/org/permissions", tags=["Org Permissions"])


@router.get("")
async def list_permissions(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
):
    return {"data": ORG_PERMISSIONS}
