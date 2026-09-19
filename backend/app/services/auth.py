import json
import uuid
from datetime import datetime, timedelta

import redis.asyncio as aioredis
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_secure_token,
    hash_password,
    verify_password,
)
from app.db.models.org import OrgSettings, Organization
from app.db.models.rbac import OrgRole, OrgRolePermission, OrgUserRole
from app.db.models.user import EmailVerificationToken, InvitationToken, OrgUser, PasswordResetToken
from app.schemas.auth import (
    AcceptInviteRequest,
    AuthResponse,
    ForgotPasswordResponse,
    SignUpRequest,
    SignUpResponse,
)
from app.schemas.user import UserOut
from app.services.email import send_invite_email, send_password_reset_email, send_verification_email
from app.services.rbac import ORG_PERMISSIONS, build_role_out


async def _load_user_with_roles(db: AsyncSession, user_id: uuid.UUID) -> OrgUser:
    result = await db.execute(
        select(OrgUser)
        .where(OrgUser.id == user_id)
        .options(selectinload(OrgUser.user_roles).selectinload(OrgUserRole.role).selectinload(OrgRole.permissions))
    )
    return result.scalar_one()


async def _create_session(
    redis: aioredis.Redis,
    user_id: uuid.UUID,
    org_id: uuid.UUID,
    user_agent: str | None,
    ip: str | None,
) -> tuple[str, str]:
    """Creates a Redis session and refresh token. Returns (session_id, refresh_token_id)."""
    session_id = str(uuid.uuid4())
    refresh_token_id = str(uuid.uuid4())
    now = datetime.utcnow()
    expires_at = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    session_data = {
        "user_id": str(user_id),
        "org_id": str(org_id),
        "user_agent": user_agent,
        "ip": ip,
        "created_at": now.isoformat(),
        "last_used_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
    }
    ttl = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400

    await redis.setex(f"session:{session_id}", ttl, json.dumps(session_data))
    await redis.sadd(f"user_sessions:{user_id}", session_id)

    refresh_data = {"user_id": str(user_id), "org_id": str(org_id), "session_id": session_id}
    await redis.setex(f"refresh:{refresh_token_id}", ttl, json.dumps(refresh_data))

    return session_id, refresh_token_id


async def _build_auth_response(
    db: AsyncSession,
    redis: aioredis.Redis,
    user: OrgUser,
    user_agent: str | None = None,
    ip: str | None = None,
) -> AuthResponse:
    user_with_roles = await _load_user_with_roles(db, user.id)
    session_id, refresh_token_id = await _create_session(redis, user.id, user.org_id, user_agent, ip)

    access_token = create_access_token({"sub": str(user.id), "org_id": str(user.org_id)})
    user_out = _user_to_schema(user_with_roles)

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token_id,
        user=user_out,
    )


def _user_to_schema(user: OrgUser) -> UserOut:
    from app.services.rbac import build_role_out
    roles = [build_role_out(ur.role) for ur in user.user_roles] if user.user_roles else []
    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        email_verified=user.email_verified,
        status=user.status,
        org_roles=roles,
        created_at=user.created_at,
    )


async def sign_up(db: AsyncSession, redis: aioredis.Redis, data: SignUpRequest) -> SignUpResponse:
    # Check email uniqueness — allow re-registration if previous account was never verified
    existing_result = await db.execute(select(OrgUser).where(OrgUser.email == data.email))
    existing = existing_result.scalar_one_or_none()
    if existing:
        if existing.email_verified:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        # Orphaned unverified account — delete it and allow re-registration
        await db.delete(existing)
        await db.flush()

    # 1. Create Organization
    org = Organization(name=data.org_name)
    db.add(org)
    await db.flush()

    # 2. Create OrgSettings
    org_settings = OrgSettings(org_id=org.id)
    db.add(org_settings)

    # 3. Seed default roles
    all_perm_keys = [p["key"] for p in ORG_PERMISSIONS]
    super_admin_role = OrgRole(org_id=org.id, name="Super Admin", is_default=True)
    db.add(super_admin_role)
    await db.flush()

    for perm_key in all_perm_keys:
        db.add(OrgRolePermission(role_id=super_admin_role.id, permission=perm_key))

    # 4. Create OrgUser
    user = OrgUser(
        org_id=org.id,
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),
        email_verified=False,
        is_super_admin=True,
    )
    db.add(user)
    await db.flush()

    # 5. Assign Super Admin role
    db.add(OrgUserRole(user_id=user.id, role_id=super_admin_role.id))

    # 6. Create EmailVerificationToken
    token_value = generate_secure_token()
    ev_token = EmailVerificationToken(
        user_id=user.id,
        token=token_value,
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )
    db.add(ev_token)
    await db.commit()

    send_verification_email(data.email, token_value)

    # Load user with roles for response
    user_with_roles = await _load_user_with_roles(db, user.id)
    user_out = _user_to_schema(user_with_roles)

    return SignUpResponse(
        user=user_out,
        message="Account created. Please check your email to verify your account.",
        verification_token=token_value,
    )


async def verify_email(db: AsyncSession, token: str) -> dict:
    result = await db.execute(
        select(EmailVerificationToken).where(EmailVerificationToken.token == token)
    )
    ev_token = result.scalar_one_or_none()

    if not ev_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token")
    if ev_token.used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token already used")
    if ev_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired")

    ev_token.used = True
    user_result = await db.execute(select(OrgUser).where(OrgUser.id == ev_token.user_id))
    user = user_result.scalar_one()
    user.email_verified = True
    await db.commit()

    return {"message": "Email verified. You can now sign in."}


async def resend_verification(db: AsyncSession, email: str) -> dict:
    result = await db.execute(select(OrgUser).where(OrgUser.email == email))
    user = result.scalar_one_or_none()

    if not user or user.email_verified:
        # Silent — return generic message
        return {"message": "If the email exists and is unverified, a token has been sent."}

    token_value = generate_secure_token()
    ev_token = EmailVerificationToken(
        user_id=user.id,
        token=token_value,
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )
    db.add(ev_token)
    await db.commit()

    send_verification_email(user.email, token_value)

    return {"message": "Verification token generated.", "verification_token": token_value}


async def sign_in(
    db: AsyncSession,
    redis: aioredis.Redis,
    email: str,
    password: str,
    user_agent: str | None = None,
    ip: str | None = None,
) -> AuthResponse:
    result = await db.execute(select(OrgUser).where(OrgUser.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Check account active
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")

    # Check email verified
    if not user.email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")

    # Check lockout
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked until {user.locked_until.isoformat()}",
        )

    # Verify password
    if not user.hashed_password or not verify_password(password, user.hashed_password):
        user.failed_login_attempts += 1

        # Load org settings to check lockout policy
        org_settings_result = await db.execute(
            select(OrgSettings).where(OrgSettings.org_id == user.org_id)
        )
        org_settings = org_settings_result.scalar_one_or_none()

        if org_settings and org_settings.lockout_enabled:
            if user.failed_login_attempts >= org_settings.lockout_max_attempts:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=org_settings.lockout_duration_minutes
                )

        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Reset failed attempts on success
    user.failed_login_attempts = 0
    user.locked_until = None
    await db.commit()

    return await _build_auth_response(db, redis, user, user_agent, ip)


async def refresh_tokens(
    db: AsyncSession,
    redis: aioredis.Redis,
    refresh_token: str,
    user_agent: str | None = None,
    ip: str | None = None,
) -> AuthResponse:
    raw = await redis.get(f"refresh:{refresh_token}")
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    data = json.loads(raw)
    user_id = uuid.UUID(data["user_id"])
    session_id = data.get("session_id")

    # Delete old refresh token
    await redis.delete(f"refresh:{refresh_token}")

    result = await db.execute(select(OrgUser).where(OrgUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Delete old session if present
    if session_id:
        await redis.delete(f"session:{session_id}")
        await redis.srem(f"user_sessions:{user_id}", session_id)

    return await _build_auth_response(db, redis, user, user_agent, ip)


async def sign_out(redis: aioredis.Redis, refresh_token: str, session_id: str | None = None) -> None:
    if refresh_token:
        raw = await redis.get(f"refresh:{refresh_token}")
        if raw:
            data = json.loads(raw)
            sid = data.get("session_id") or session_id
            if sid:
                await redis.delete(f"session:{sid}")
                user_id = data.get("user_id")
                if user_id:
                    await redis.srem(f"user_sessions:{user_id}", sid)
        await redis.delete(f"refresh:{refresh_token}")


async def forgot_password(db: AsyncSession, email: str) -> ForgotPasswordResponse:
    result = await db.execute(select(OrgUser).where(OrgUser.email == email))
    user = result.scalar_one_or_none()

    if not user:
        # Silent — still return a token-like response shape (dummy)
        return ForgotPasswordResponse(reset_token="")

    token_value = generate_secure_token()
    pr_token = PasswordResetToken(
        user_id=user.id,
        token=token_value,
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db.add(pr_token)
    await db.commit()

    send_password_reset_email(user.email, token_value)

    return ForgotPasswordResponse(reset_token=token_value)


async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
    result = await db.execute(select(PasswordResetToken).where(PasswordResetToken.token == token))
    pr_token = result.scalar_one_or_none()

    if not pr_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token")
    if pr_token.used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token already used")
    if pr_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired")

    user_result = await db.execute(select(OrgUser).where(OrgUser.id == pr_token.user_id))
    user = user_result.scalar_one()

    user.hashed_password = hash_password(new_password)
    user.tokens_invalidated_at = datetime.utcnow()
    pr_token.used = True
    await db.commit()


async def accept_invite(
    db: AsyncSession,
    redis: aioredis.Redis,
    data: AcceptInviteRequest,
    user_agent: str | None = None,
    ip: str | None = None,
) -> AuthResponse:
    result = await db.execute(
        select(InvitationToken).where(InvitationToken.token == data.token)
    )
    inv_token = result.scalar_one_or_none()

    if not inv_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid invitation token")
    if inv_token.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation is not pending")
    if inv_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation expired")

    user_result = await db.execute(select(OrgUser).where(OrgUser.id == inv_token.user_id))
    user = user_result.scalar_one()

    user.hashed_password = hash_password(data.password)
    if data.name:
        user.name = data.name
    user.email_verified = True

    inv_token.status = "accepted"
    inv_token.accepted_at = datetime.utcnow()
    await db.commit()

    return await _build_auth_response(db, redis, user, user_agent, ip)
