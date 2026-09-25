import json
import uuid
from datetime import datetime, timedelta

import redis.asyncio as aioredis
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, generate_secure_token, hash_password, verify_password
from app.db.models.citizen import Citizen, CitizenEmailVerificationToken, CitizenPasswordResetToken
from app.db.models.org import Organization
from app.db.models.portal import Portal
from app.schemas.citizen import (
    CitizenAuthResponse,
    CitizenOut,
    CitizenSignUpRequest,
    CitizenSignUpResponse,
)
from app.services.email import send_verification_email, send_password_reset_email


async def _get_org_by_slug(db: AsyncSession, org_slug: str) -> Organization:
    org = (await db.execute(select(Organization).where(Organization.slug == org_slug))).scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portal not found")
    return org


async def _get_portal_by_slug(db: AsyncSession, org_slug: str, portal_slug: str) -> Portal:
    org = await _get_org_by_slug(db, org_slug)
    portal = (await db.execute(
        select(Portal).where(Portal.org_id == org.id, Portal.slug == portal_slug)
    )).scalar_one_or_none()
    if not portal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portal not found")
    return portal


async def _create_citizen_session(
    redis: aioredis.Redis,
    citizen_id: uuid.UUID,
    portal_id: uuid.UUID,
) -> tuple[str, str]:
    session_id = str(uuid.uuid4())
    refresh_token_id = str(uuid.uuid4())
    now = datetime.utcnow()
    expires_at = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    ttl = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400

    session_data = {
        "citizen_id": str(citizen_id),
        "portal_id": str(portal_id),
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
    }
    await redis.setex(f"citizen_session:{session_id}", ttl, json.dumps(session_data))

    refresh_data = {"citizen_id": str(citizen_id), "portal_id": str(portal_id), "session_id": session_id}
    await redis.setex(f"citizen_refresh:{refresh_token_id}", ttl, json.dumps(refresh_data))

    return session_id, refresh_token_id


async def _build_citizen_auth_response(
    db: AsyncSession, redis: aioredis.Redis, citizen: Citizen, portal_id: uuid.UUID
) -> CitizenAuthResponse:
    _, refresh_token_id = await _create_citizen_session(redis, citizen.id, portal_id)
    access_token = create_access_token({
        "sub": str(citizen.id),
        "portal_id": str(portal_id),
        "type": "citizen",
    })
    return CitizenAuthResponse(
        access_token=access_token,
        refresh_token=refresh_token_id,
        citizen=CitizenOut.model_validate(citizen),
    )


async def sign_up(
    db: AsyncSession, redis: aioredis.Redis, org_slug: str, portal_slug: str, data: CitizenSignUpRequest
) -> CitizenSignUpResponse:
    # Validate the portal exists (so sign-up on an invalid URL fails)
    portal = await _get_portal_by_slug(db, org_slug, portal_slug)
    org_id = portal.org_id

    existing = (await db.execute(
        select(Citizen).where(Citizen.org_id == org_id, Citizen.email == data.email)
    )).scalar_one_or_none()

    if existing:
        if existing.email_verified:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        await db.delete(existing)
        await db.flush()

    citizen = Citizen(
        org_id=org_id,
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),
        email_verified=False,
    )
    db.add(citizen)
    await db.flush()

    token_value = generate_secure_token()
    ev_token = CitizenEmailVerificationToken(
        citizen_id=citizen.id,
        token=token_value,
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )
    db.add(ev_token)
    await db.commit()

    send_verification_email(citizen.email, token_value, org_slug, portal_slug)

    return CitizenSignUpResponse(
        citizen=CitizenOut.model_validate(citizen),
        message="Account created. Please check your email to verify your account.",
    )


async def verify_email(db: AsyncSession, token: str) -> dict:
    ev_token = (await db.execute(
        select(CitizenEmailVerificationToken).where(CitizenEmailVerificationToken.token == token)
    )).scalar_one_or_none()

    if not ev_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token")
    if ev_token.used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token already used")
    if ev_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired")

    ev_token.used = True
    citizen = (await db.execute(select(Citizen).where(Citizen.id == ev_token.citizen_id))).scalar_one()
    citizen.email_verified = True
    await db.commit()

    return {"message": "Email verified. You can now sign in."}


async def sign_in(
    db: AsyncSession, redis: aioredis.Redis, org_slug: str, portal_slug: str, email: str, password: str
) -> CitizenAuthResponse:
    portal = await _get_portal_by_slug(db, org_slug, portal_slug)

    citizen = (await db.execute(
        select(Citizen).where(Citizen.org_id == portal.org_id, Citizen.email == email)
    )).scalar_one_or_none()

    if not citizen:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if citizen.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")
    if not citizen.email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")
    if citizen.locked_until and citizen.locked_until > datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=f"Account locked until {citizen.locked_until.isoformat()}")

    if not citizen.hashed_password or not verify_password(password, citizen.hashed_password):
        citizen.failed_login_attempts += 1
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    citizen.failed_login_attempts = 0
    citizen.locked_until = None
    await db.commit()

    return await _build_citizen_auth_response(db, redis, citizen, portal.id)


async def refresh_tokens(
    db: AsyncSession, redis: aioredis.Redis, refresh_token: str
) -> CitizenAuthResponse:
    raw = await redis.get(f"citizen_refresh:{refresh_token}")
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    data = json.loads(raw)
    citizen_id = uuid.UUID(data["citizen_id"])
    portal_id = uuid.UUID(data["portal_id"])
    session_id = data.get("session_id")

    await redis.delete(f"citizen_refresh:{refresh_token}")
    session_raw = None
    if session_id:
        session_raw = await redis.get(f"citizen_session:{session_id}")
        await redis.delete(f"citizen_session:{session_id}")

    citizen = (await db.execute(select(Citizen).where(Citizen.id == citizen_id))).scalar_one_or_none()
    if not citizen:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Citizen not found")

    if citizen.tokens_invalidated_at and session_id and session_raw:
        session_data = json.loads(session_raw)
        session_created_at = datetime.fromisoformat(session_data["created_at"])
        if session_created_at < citizen.tokens_invalidated_at:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session has been invalidated")

    return await _build_citizen_auth_response(db, redis, citizen, portal_id)


async def sign_out(redis: aioredis.Redis, refresh_token: str) -> None:
    raw = await redis.get(f"citizen_refresh:{refresh_token}")
    if raw:
        data = json.loads(raw)
        session_id = data.get("session_id")
        if session_id:
            await redis.delete(f"citizen_session:{session_id}")
    await redis.delete(f"citizen_refresh:{refresh_token}")


async def forgot_password(db: AsyncSession, org_slug: str, portal_slug: str, email: str) -> dict:
    portal = await _get_portal_by_slug(db, org_slug, portal_slug)

    citizen = (await db.execute(
        select(Citizen).where(Citizen.org_id == portal.org_id, Citizen.email == email)
    )).scalar_one_or_none()

    if not citizen:
        return {"message": "If the email exists, a reset link has been sent."}

    token_value = generate_secure_token()
    pr_token = CitizenPasswordResetToken(
        citizen_id=citizen.id,
        token=token_value,
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db.add(pr_token)
    await db.commit()

    send_password_reset_email(citizen.email, token_value, org_slug, portal_slug)
    return {"message": "If the email exists, a reset link has been sent."}


async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
    pr_token = (await db.execute(
        select(CitizenPasswordResetToken).where(CitizenPasswordResetToken.token == token)
    )).scalar_one_or_none()

    if not pr_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token")
    if pr_token.used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token already used")
    if pr_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired")

    citizen = (await db.execute(select(Citizen).where(Citizen.id == pr_token.citizen_id))).scalar_one()
    citizen.hashed_password = hash_password(new_password)
    citizen.tokens_invalidated_at = datetime.utcnow()
    pr_token.used = True
    await db.commit()
