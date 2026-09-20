import uuid
from datetime import datetime

from pydantic import BaseModel


class PortalCreate(BaseModel):
    name: str
    description: str | None = None
    domain: str | None = None


class PortalUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    domain: str | None = None


class PortalOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    domain: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PortalRoleCreate(BaseModel):
    name: str
    description: str | None = None
    permissions: list[str] = []


class PortalRoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    permissions: list[str] | None = None


class PortalRoleOut(BaseModel):
    id: uuid.UUID
    portal_id: uuid.UUID
    name: str
    description: str | None
    permissions: list[str]
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AssignPortalUserRequest(BaseModel):
    user_id: uuid.UUID
    role_id: uuid.UUID


class PortalUserOut(BaseModel):
    user_id: uuid.UUID
    name: str | None
    email: str
    role: PortalRoleOut

    model_config = {"from_attributes": True}


class RequestTypeCreate(BaseModel):
    name: str
    description: str | None = None


class RequestTypeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class RequestTypeOut(BaseModel):
    id: uuid.UUID
    portal_id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RequestOut(BaseModel):
    id: uuid.UUID
    portal_id: uuid.UUID
    request_type_id: uuid.UUID
    citizen_id: uuid.UUID
    title: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RequestUpdate(BaseModel):
    status: str | None = None
    title: str | None = None
