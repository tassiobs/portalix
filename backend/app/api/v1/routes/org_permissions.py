from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_active_user
from app.db.models.user import OrgUser
from app.schemas.rbac import PermissionListOut
from app.services.rbac import ORG_PERMISSIONS

router = APIRouter(prefix="/org/permissions", tags=["Org Permissions"])

_401 = {401: {"description": "Missing or invalid authentication token"}}


@router.get(
    "",
    response_model=PermissionListOut,
    summary="List org-level permissions",
    description="Returns all available org-level permission keys with labels and descriptions. "
                "Use this to populate a permissions picker when creating or editing roles. "
                "Only permission keys from this list are valid for org-level roles.",
    responses={**_401},
)
async def list_permissions(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
):
    return {"data": ORG_PERMISSIONS}
