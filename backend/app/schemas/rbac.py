from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    level: str = "org"
    permissions: list[str]
    is_default: bool
    created_at: datetime


class RoleCreate(BaseModel):
    name: str
    description: str | None = None
    level: str = "org"
    permissions: list[str] = []


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    permissions: list[str] | None = None


class AssignRoleRequest(BaseModel):
    role_id: UUID
