from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_permissions
from app.db.models.user import OrgUser
from app.schemas.auth import MessageOut
from app.schemas.user import InvitationOut, InvitationPage, PaginationOut
from app.services import user as user_service

router = APIRouter(prefix="/org/invitations", tags=["Org Invitations"])

_401 = {401: {"description": "Missing or invalid authentication token"}}
_403 = {403: {"description": "Requires `org.users.manage` permission"}}
_404 = {404: {"description": "Invitation not found"}}


@router.get(
    "",
    response_model=InvitationPage,
    summary="List pending invitations",
    description="Returns a paginated list of invitations that have not yet been accepted.",
    responses={**_401},
)
async def list_invitations(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
):
    return await user_service.list_invitations(db, current_user.org_id, page, per_page)


@router.post(
    "/{invitation_id}/resend",
    response_model=MessageOut,
    summary="Resend invitation email",
    description="Sends a new invitation email for an existing pending invitation. "
                "Requires `org.users.manage`.",
    responses={**_401, **_403, **_404},
)
async def resend_invitation(
    invitation_id: UUID,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await user_service.resend_invitation(db, current_user.org_id, invitation_id)


@router.post(
    "/{invitation_id}/cancel",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel an invitation",
    description="Cancels a pending invitation so the token in the email can no longer be used. "
                "Requires `org.users.manage`.",
    responses={**_401, **_403, **_404},
)
async def cancel_invitation(
    invitation_id: UUID,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await user_service.cancel_invitation(db, current_user.org_id, invitation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
