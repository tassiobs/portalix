from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserSummary


class OrgOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    created_at: datetime


class OrgUpdate(BaseModel):
    name: str


class LockoutSettingsOut(BaseModel):
    enabled: bool
    max_failed_attempts: int
    lockout_duration_minutes: int


class LockoutSettingsUpdate(BaseModel):
    enabled: bool | None = None
    max_failed_attempts: int | None = None
    lockout_duration_minutes: int | None = None


class MfaSettingsOut(BaseModel):
    enabled: bool
    required: bool


class MfaSettingsUpdate(BaseModel):
    enabled: bool | None = None
    required: bool | None = None


class OrgSettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    citizen_identity_scope: str
    lockout: LockoutSettingsOut | None = None
    mfa: MfaSettingsOut | None = None
    updated_at: datetime | None = None
    updated_by: UserSummary | None = None


class OrgSettingsUpdate(BaseModel):
    citizen_identity_scope: str | None = None
    lockout: LockoutSettingsUpdate | None = None
    mfa: MfaSettingsUpdate | None = None
