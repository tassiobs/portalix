from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.rbac import RoleOut


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str | None = None
    email: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str | None = None
    email: str
    email_verified: bool
    status: str
    org_roles: list[RoleOut] = []
    portal_roles: list[RoleOut] = []
    created_at: datetime


class OrgUserCreate(BaseModel):
    name: str | None = Field(None, max_length=100, description="Full name of the user", example="Jane Doe")
    email: EmailStr = Field(..., description="Email address — an invitation will be sent to this address", example="jane@acme.com")


class OrgUserUpdate(BaseModel):
    name: str | None = Field(None, max_length=100, description="Updated full name of the user")
    status: Literal["active", "inactive"] | None = Field(None, description="Updated status of the user account")


class PaginationOut(BaseModel):
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=100, description="Number of items per page")
    total: int = Field(..., ge=0, description="Total number of items across all pages")
    total_pages: int = Field(..., ge=0, description="Total number of pages")


class OrgUserPage(BaseModel):
    data: list[UserOut]
    pagination: PaginationOut


class InvitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str | None = None
    status: str
    invited_by: UserSummary | None = None
    created_at: datetime
    expires_at: datetime
    accepted_at: datetime | None = None


class InvitationPage(BaseModel):
    data: list[InvitationOut]
    pagination: PaginationOut


class OrgUserCreateResponse(UserOut):
    pass
