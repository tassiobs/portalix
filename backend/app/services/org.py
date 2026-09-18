import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.org import OrgSettings, Organization
from app.db.models.user import OrgUser
from app.schemas.org import (
    OrgOut,
    OrgSettingsOut,
    OrgSettingsUpdate,
    OrgUpdate,
    LockoutSettingsOut,
    MfaSettingsOut,
)
from app.schemas.user import UserSummary


async def get_org(db: AsyncSession, org_id: uuid.UUID) -> OrgOut:
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return OrgOut.model_validate(org)


async def update_org(db: AsyncSession, org_id: uuid.UUID, data: OrgUpdate) -> OrgOut:
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    org.name = data.name
    await db.commit()
    await db.refresh(org)
    return OrgOut.model_validate(org)


def _settings_to_schema(settings_obj: OrgSettings) -> OrgSettingsOut:
    lockout = LockoutSettingsOut(
        enabled=settings_obj.lockout_enabled,
        max_failed_attempts=settings_obj.lockout_max_attempts,
        lockout_duration_minutes=settings_obj.lockout_duration_minutes,
    )
    mfa = MfaSettingsOut(enabled=settings_obj.mfa_enabled, required=settings_obj.mfa_required)

    updated_by = None
    if settings_obj.updated_by:
        updated_by = UserSummary(
            id=settings_obj.updated_by.id,
            name=settings_obj.updated_by.name,
            email=settings_obj.updated_by.email,
        )

    return OrgSettingsOut(
        citizen_identity_scope=settings_obj.citizen_identity_scope,
        lockout=lockout,
        mfa=mfa,
        updated_at=settings_obj.updated_at,
        updated_by=updated_by,
    )


async def get_org_settings(db: AsyncSession, org_id: uuid.UUID) -> OrgSettingsOut:
    result = await db.execute(
        select(OrgSettings)
        .where(OrgSettings.org_id == org_id)
        .options(selectinload(OrgSettings.updated_by))
    )
    settings_obj = result.scalar_one_or_none()
    if not settings_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Org settings not found")

    return _settings_to_schema(settings_obj)


async def update_org_settings(
    db: AsyncSession,
    org_id: uuid.UUID,
    data: OrgSettingsUpdate,
    updated_by_user: OrgUser,
) -> OrgSettingsOut:
    result = await db.execute(
        select(OrgSettings)
        .where(OrgSettings.org_id == org_id)
        .options(selectinload(OrgSettings.updated_by))
    )
    settings_obj = result.scalar_one_or_none()
    if not settings_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Org settings not found")

    if data.citizen_identity_scope is not None:
        settings_obj.citizen_identity_scope = data.citizen_identity_scope

    if data.lockout is not None:
        if data.lockout.enabled is not None:
            settings_obj.lockout_enabled = data.lockout.enabled
        if data.lockout.max_failed_attempts is not None:
            settings_obj.lockout_max_attempts = data.lockout.max_failed_attempts
        if data.lockout.lockout_duration_minutes is not None:
            settings_obj.lockout_duration_minutes = data.lockout.lockout_duration_minutes

    if data.mfa is not None:
        if data.mfa.enabled is not None:
            settings_obj.mfa_enabled = data.mfa.enabled
        if data.mfa.required is not None:
            settings_obj.mfa_required = data.mfa.required

    settings_obj.updated_at = datetime.utcnow()
    settings_obj.updated_by_id = updated_by_user.id
    await db.commit()

    # Reload with updated_by
    result = await db.execute(
        select(OrgSettings)
        .where(OrgSettings.org_id == org_id)
        .options(selectinload(OrgSettings.updated_by))
    )
    settings_obj = result.scalar_one()
    return _settings_to_schema(settings_obj)
