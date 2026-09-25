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


class AssignPortalUserRequest(BaseModel):
    user_id: uuid.UUID
    role_id: uuid.UUID


VALID_FIELD_TYPES = {"text", "textarea", "number", "date", "select"}


class RequestTypeFieldCreate(BaseModel):
    label: str
    field_type: str
    required: bool = False
    order: int = 0
    options: list[str] | None = None


class RequestTypeFieldUpdate(BaseModel):
    label: str | None = None
    field_type: str | None = None
    required: bool | None = None
    order: int | None = None
    options: list[str] | None = None


class RequestTypeFieldOut(BaseModel):
    id: uuid.UUID
    request_type_id: uuid.UUID
    label: str
    field_type: str
    required: bool
    order: int
    options: list[str] | None
    created_at: datetime

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
    fields: list[RequestTypeFieldOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class RequestFieldValueOut(BaseModel):
    field_id: uuid.UUID
    label: str
    field_type: str
    value: str | None

    model_config = {"from_attributes": True}


class RequestFieldValueSubmit(BaseModel):
    field_id: uuid.UUID
    value: str | None = None


class RequestOut(BaseModel):
    id: uuid.UUID
    portal_id: uuid.UUID
    request_type_id: uuid.UUID
    request_type_name: str | None = None
    citizen_id: uuid.UUID
    title: str
    status: str
    field_values: list[RequestFieldValueOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class RequestUpdate(BaseModel):
    status: str | None = None
    title: str | None = None
