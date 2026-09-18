from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_permissions
from app.db.models.user import OrgUser
from app.schemas.user import InvitationOut, PaginationOut
from app.services import user as user_service

router = APIRouter(prefix="/org/invitations", tags=["Org Invitations"])


@router.get("")
async def list_invitations(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    return await user_service.list_invitations(db, current_user.org_id, page, per_page)


@router.post("/{invitation_id}/resend")
async def resend_invitation(
    invitation_id: UUID,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await user_service.resend_invitation(db, current_user.org_id, invitation_id)


@router.post("/{invitation_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_invitation(
    invitation_id: UUID,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await user_service.cancel_invitation(db, current_user.org_id, invitation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
