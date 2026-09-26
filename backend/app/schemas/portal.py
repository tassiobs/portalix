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


# --- Workflow schemas ---

class TaskDefinitionIn(BaseModel):
    key: str
    name: str
    department_id: uuid.UUID | None = None
    assignee_role: str | None = None
    assignee_user_id: uuid.UUID | None = None
    deadline_offset_hours: int | None = None
    depends_on: list[str] = []
    fan_out: bool = False


class TaskDefinitionOut(BaseModel):
    id: uuid.UUID
    key: str
    name: str
    department_id: uuid.UUID | None
    assignee_role: str | None
    assignee_user_id: uuid.UUID | None
    deadline_offset_hours: int | None
    depends_on: list[str]
    fan_out: bool

    model_config = {"from_attributes": True}


class WorkflowIn(BaseModel):
    tasks: list[TaskDefinitionIn]


class WorkflowOut(BaseModel):
    id: uuid.UUID
    request_type_id: uuid.UUID
    tasks: list[TaskDefinitionOut]
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskCommentIn(BaseModel):
    body: str | None = None
    file_url: str | None = None
    file_name: str | None = None


class TaskCommentOut(BaseModel):
    id: uuid.UUID
    task_instance_id: uuid.UUID
    author_user_id: uuid.UUID | None
    body: str | None
    file_url: str | None
    file_name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskInstanceOut(BaseModel):
    id: uuid.UUID
    request_id: uuid.UUID
    task_definition: TaskDefinitionOut
    status: str
    outcome: str | None
    assigned_to_user_id: uuid.UUID | None
    activated_at: datetime | None
    deadline: datetime | None
    completed_at: datetime | None
    completion_notes: str | None
    comments: list[TaskCommentOut] = []

    model_config = {"from_attributes": True}


class TaskInstanceUpdate(BaseModel):
    assigned_to_user_id: uuid.UUID | None = None


class TaskCompleteIn(BaseModel):
    outcome: str
    notes: str | None = None
