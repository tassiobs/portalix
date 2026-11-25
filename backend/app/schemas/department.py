import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserSummary


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Name of the department", example="Legal")
    description: str | None = Field(None, max_length=500, description="Optional description of the department")


class DepartmentUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100, description="Updated name of the department")
    description: str | None = Field(None, max_length=500, description="Updated description")


class DepartmentMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user: UserSummary
    created_at: datetime


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    description: str | None
    member_count: int = 0
    created_at: datetime


class DepartmentDetailOut(DepartmentOut):
    members: list[DepartmentMemberOut] = []


class AddMemberRequest(BaseModel):
    user_id: uuid.UUID = Field(..., description="ID of the org user to add to the department")
