from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    level: str = "org"
    permissions: list[str]
    is_default: bool
    portal_id: UUID | None = None
    portal_name: str | None = None
    created_at: datetime


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Name of the role", example="Case Manager")
    description: str | None = Field(None, max_length=500, description="Optional description of what this role can do", example="Can manage and update citizen requests")
    level: Literal["org", "portal"] = Field("org", description="Scope of the role — 'org' applies across the organization, 'portal' is scoped to a specific portal")
    permissions: list[str] = Field([], description="List of permission keys granted to this role", example=["requests:read", "requests:write"])


class RoleUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100, description="Name of the role")
    description: str | None = Field(None, max_length=500, description="Optional description of what this role can do")
    permissions: list[str] | None = Field(None, description="Full list of permission keys — replaces existing permissions")


class AssignRoleRequest(BaseModel):
    role_id: UUID = Field(..., description="ID of the role to assign to the user")
