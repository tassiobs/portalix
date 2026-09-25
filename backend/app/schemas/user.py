from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

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
    name: str | None = None
    email: EmailStr


class OrgUserUpdate(BaseModel):
    name: str | None = None
    status: str | None = None


class PaginationOut(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int


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


class OrgUserCreateResponse(UserOut):
    pass
