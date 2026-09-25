import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import generate_secure_token
from app.db.models.org import Organization
from app.db.models.portal import Portal, PortalUserRole
from app.db.models.rbac import OrgRole, OrgUserRole
from app.db.models.user import InvitationToken, OrgUser
from app.services.email import send_invite_email
from app.schemas.user import (
    InvitationOut,
    OrgUserCreate,
    OrgUserCreateResponse,
    OrgUserPage,
    OrgUserUpdate,
    PaginationOut,
    UserOut,
    UserSummary,
)
from app.services.rbac import build_role_out


def _user_to_out(user: OrgUser, portal_roles: list | None = None) -> UserOut:
    org_roles = [build_role_out(ur.role) for ur in user.user_roles] if user.user_roles else []
    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        email_verified=user.email_verified,
        status=user.status,
        org_roles=org_roles,
        portal_roles=portal_roles or [],
        created_at=user.created_at,
    )


async def _get_portal_roles(db: AsyncSession, user_id: uuid.UUID) -> list:
    result = await db.execute(
        select(PortalUserRole)
        .where(PortalUserRole.user_id == user_id)
        .options(
            selectinload(PortalUserRole.role).selectinload(OrgRole.permissions),
            selectinload(PortalUserRole.portal),
        )
    )
    roles = []
    for pur in result.scalars().all():
        role_out = build_role_out(pur.role)
        role_out.portal_id = pur.portal_id
        role_out.portal_name = pur.portal.name if pur.portal else None
        roles.append(role_out)
    return roles


async def _load_user(db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID) -> OrgUser:
    result = await db.execute(
        select(OrgUser)
        .where(OrgUser.id == user_id, OrgUser.org_id == org_id)
        .options(selectinload(OrgUser.user_roles).selectinload(OrgUserRole.role).selectinload(OrgRole.permissions))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


async def list_users(
    db: AsyncSession, org_id: uuid.UUID, page: int = 1, per_page: int = 20
) -> OrgUserPage:
    offset = (page - 1) * per_page

    count_result = await db.execute(
        select(func.count()).select_from(OrgUser).where(OrgUser.org_id == org_id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(OrgUser)
        .where(OrgUser.org_id == org_id)
        .options(selectinload(OrgUser.user_roles).selectinload(OrgUserRole.role).selectinload(OrgRole.permissions))
        .offset(offset)
        .limit(per_page)
        .order_by(OrgUser.created_at)
    )
    users = result.scalars().all()
    total_pages = max(1, (total + per_page - 1) // per_page)

    user_outs = []
    for u in users:
        portal_roles = await _get_portal_roles(db, u.id)
        user_outs.append(_user_to_out(u, portal_roles))

    return OrgUserPage(
        data=user_outs,
        pagination=PaginationOut(page=page, per_page=per_page, total=total, total_pages=total_pages),
    )


async def create_user(
    db: AsyncSession,
    org_id: uuid.UUID,
    data: OrgUserCreate,
    invited_by: OrgUser,
) -> OrgUserCreateResponse:
    existing_user = (await db.execute(
        select(OrgUser).where(OrgUser.email == data.email)
    )).scalar_one_or_none()

    if existing_user:
        # Allow re-invite if the user belongs to this org and never accepted
        if existing_user.org_id != org_id or existing_user.hashed_password is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        # Refresh or create a pending invitation token
        existing_inv = (await db.execute(
            select(InvitationToken)
            .where(InvitationToken.user_id == existing_user.id, InvitationToken.status == "pending")
        )).scalar_one_or_none()

        org_result = await db.execute(select(Organization).where(Organization.id == org_id))
        org = org_result.scalar_one()
        token_value = generate_secure_token()

        if existing_inv:
            existing_inv.token = token_value
            existing_inv.status = "pending"
            existing_inv.expires_at = datetime.utcnow() + timedelta(days=7)
        else:
            db.add(InvitationToken(
                user_id=existing_user.id,
                org_id=org_id,
                email=data.email,
                name=data.name,
                token=token_value,
                status="pending",
                invited_by_id=invited_by.id,
                expires_at=datetime.utcnow() + timedelta(days=7),
            ))

        await db.commit()
        send_invite_email(data.email, token_value, org.name)

        user_loaded = await _load_user(db, org_id, existing_user.id)
        portal_roles = await _get_portal_roles(db, existing_user.id)
        user_out = _user_to_out(user_loaded, portal_roles)
        return OrgUserCreateResponse(**user_out.model_dump())

    user = OrgUser(
        org_id=org_id,
        name=data.name,
        email=data.email,
        hashed_password=None,
        email_verified=False,
    )
    db.add(user)
    await db.flush()

    token_value = generate_secure_token()
    inv_token = InvitationToken(
        user_id=user.id,
        org_id=org_id,
        email=data.email,
        name=data.name,
        token=token_value,
        status="pending",
        invited_by_id=invited_by.id,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(inv_token)
    await db.commit()

    org_result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = org_result.scalar_one()
    send_invite_email(data.email, token_value, org.name)

    user_loaded = await _load_user(db, org_id, user.id)
    portal_roles = await _get_portal_roles(db, user.id)
    user_out = _user_to_out(user_loaded, portal_roles)

    return OrgUserCreateResponse(**user_out.model_dump())


async def get_user(db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID) -> UserOut:
    user = await _load_user(db, org_id, user_id)
    portal_roles = await _get_portal_roles(db, user_id)
    return _user_to_out(user, portal_roles)


async def update_user(
    db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID, data: OrgUserUpdate
) -> UserOut:
    user = await _load_user(db, org_id, user_id)

    if data.name is not None:
        user.name = data.name
    if data.status is not None:
        user.status = data.status

    await db.commit()
    user_reloaded = await _load_user(db, org_id, user_id)
    portal_roles = await _get_portal_roles(db, user_id)
    return _user_to_out(user_reloaded, portal_roles)


async def deactivate_user(db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID) -> None:
    user = await _load_user(db, org_id, user_id)
    user.status = "inactive"
    await db.commit()


async def get_profile(db: AsyncSession, user: OrgUser) -> UserOut:
    loaded = await _load_user(db, user.org_id, user.id)
    portal_roles = await _get_portal_roles(db, user.id)
    return _user_to_out(loaded, portal_roles)


async def update_profile(db: AsyncSession, user: OrgUser, data: OrgUserUpdate) -> UserOut:
    loaded = await _load_user(db, user.org_id, user.id)

    if data.name is not None:
        loaded.name = data.name

    await db.commit()
    reloaded = await _load_user(db, user.org_id, user.id)
    portal_roles = await _get_portal_roles(db, user.id)
    return _user_to_out(reloaded, portal_roles)


async def list_invitations(
    db: AsyncSession,
    org_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
) -> dict:
    offset = (page - 1) * per_page

    count_result = await db.execute(
        select(func.count()).select_from(InvitationToken).where(InvitationToken.org_id == org_id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(InvitationToken)
        .where(InvitationToken.org_id == org_id)
        .options(selectinload(InvitationToken.invited_by))
        .offset(offset)
        .limit(per_page)
        .order_by(InvitationToken.created_at.desc())
    )
    invitations = result.scalars().all()
    total_pages = max(1, (total + per_page - 1) // per_page)

    data = [_invitation_to_out(inv) for inv in invitations]
    return {
        "data": data,
        "pagination": PaginationOut(page=page, per_page=per_page, total=total, total_pages=total_pages),
    }


def _invitation_to_out(inv: InvitationToken) -> InvitationOut:
    invited_by = None
    if inv.invited_by:
        invited_by = UserSummary(id=inv.invited_by.id, name=inv.invited_by.name, email=inv.invited_by.email)
    return InvitationOut(
        id=inv.id,
        email=inv.email,
        name=inv.name,
        status=inv.status,
        invited_by=invited_by,
        created_at=inv.created_at,
        expires_at=inv.expires_at,
        accepted_at=inv.accepted_at,
    )


async def resend_invitation(
    db: AsyncSession, org_id: uuid.UUID, invitation_id: uuid.UUID
) -> dict:
    result = await db.execute(
        select(InvitationToken)
        .where(InvitationToken.id == invitation_id, InvitationToken.org_id == org_id)
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
    if inv.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation is not pending")

    new_token = generate_secure_token()
    inv.token = new_token
    inv.status = "pending"
    inv.expires_at = datetime.utcnow() + timedelta(days=7)
    await db.commit()

    org_result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = org_result.scalar_one()
    send_invite_email(inv.email, new_token, org.name)

    return {"message": "Invitation resent."}


async def cancel_invitation(
    db: AsyncSession, org_id: uuid.UUID, invitation_id: uuid.UUID
) -> None:
    result = await db.execute(
        select(InvitationToken)
        .where(InvitationToken.id == invitation_id, InvitationToken.org_id == org_id)
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
    if inv.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation is not pending")

    inv.status = "cancelled"
    await db.commit()
