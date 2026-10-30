from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserSummary


class OrgOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    created_at: datetime


class OrgUpdate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Display name of the organization", example="Acme Corp")


class LockoutSettingsOut(BaseModel):
    enabled: bool
    max_failed_attempts: int
    lockout_duration_minutes: int


class LockoutSettingsUpdate(BaseModel):
    enabled: bool | None = Field(None, description="Whether account lockout is enabled")
    max_failed_attempts: int | None = Field(None, ge=1, le=20, description="Number of failed login attempts before lockout", example=5)
    lockout_duration_minutes: int | None = Field(None, ge=1, description="How long the account remains locked in minutes", example=30)


class MfaSettingsOut(BaseModel):
    enabled: bool
    required: bool


class MfaSettingsUpdate(BaseModel):
    enabled: bool | None = Field(None, description="Whether MFA is available for users")
    required: bool | None = Field(None, description="Whether MFA is mandatory for all users")


class OrgSettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    citizen_identity_scope: str
    lockout: LockoutSettingsOut | None = None
    mfa: MfaSettingsOut | None = None
    updated_at: datetime | None = None
    updated_by: UserSummary | None = None


class OrgSettingsUpdate(BaseModel):
    citizen_identity_scope: Literal["portal", "org"] | None = Field(
        None, description="Controls whether citizen accounts are scoped to a single portal or shared across the org"
    )
    lockout: LockoutSettingsUpdate | None = Field(None, description="Account lockout policy settings")
    mfa: MfaSettingsUpdate | None = Field(None, description="Multi-factor authentication settings")
