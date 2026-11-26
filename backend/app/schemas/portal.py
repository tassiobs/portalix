import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PortalCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Display name of the portal", example="Citizens Portal")
    slug: str | None = Field(None, min_length=2, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", description="URL-friendly identifier for the portal. Auto-generated from name if not provided.", example="citizens-portal")
    description: str | None = Field(None, max_length=500, description="Optional description of the portal's purpose", example="Public-facing portal for citizen service requests")
    domain: str | None = Field(None, description="Custom domain for the portal (e.g. portal.acme.com)", example="portal.acme.com")


class PortalUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100, description="Display name of the portal", example="Citizens Portal")
    slug: str | None = Field(None, min_length=2, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", description="URL-friendly identifier for the portal. Must be unique within the org.", example="citizens-portal")
    description: str | None = Field(None, max_length=500, description="Optional description of the portal's purpose")
    domain: str | None = Field(None, description="Custom domain for the portal", example="portal.acme.com")


class PortalOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    domain: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PortalPublicOut(BaseModel):
    name: str
    slug: str
    description: str | None
    org_slug: str

    model_config = {"from_attributes": True}


class AssignPortalUserRequest(BaseModel):
    user_id: uuid.UUID = Field(..., description="ID of the user to assign to the portal")
    role_id: uuid.UUID = Field(..., description="ID of the portal-level role to assign")


VALID_FIELD_TYPES = {"text", "textarea", "number", "date", "select", "file"}


class RequestTypeFieldCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=200, description="Display label for the field", example="Full Name")
    field_type: Literal["text", "textarea", "number", "date", "select", "file"] = Field(
        ..., description="Input type for the field"
    )
    required: bool = Field(False, description="Whether this field must be filled in when submitting a request")
    order: int = Field(0, ge=0, description="Display order position (0-indexed)", example=0)
    options: list[str] | None = Field(None, description="Allowed options — required when field_type is 'select'", example=["Option A", "Option B"])


class RequestTypeFieldUpdate(BaseModel):
    label: str | None = Field(None, min_length=1, max_length=200, description="Display label for the field")
    field_type: Literal["text", "textarea", "number", "date", "select", "file"] | None = Field(
        None, description="Input type for the field"
    )
    required: bool | None = Field(None, description="Whether this field must be filled in when submitting a request")
    order: int | None = Field(None, ge=0, description="Display order position (0-indexed)")
    options: list[str] | None = Field(None, description="Allowed options — required when field_type is 'select'")


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
    name: str = Field(..., min_length=2, max_length=100, description="Name of the request type", example="Building Permit")
    description: str | None = Field(None, max_length=500, description="Optional description of what this request type is for", example="Request a permit for construction or renovation")


class RequestTypeUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100, description="Name of the request type")
    description: str | None = Field(None, max_length=500, description="Optional description")


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
    field_id: uuid.UUID = Field(..., description="ID of the request type field being answered")
    value: str | None = Field(None, max_length=5000, description="Value submitted for this field")


class RequestOut(BaseModel):
    id: uuid.UUID
    number: int
    reference: str
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
    status: Literal["open", "in_progress", "rejected", "closed"] | None = Field(
        None, description="Updated status for the request"
    )
    title: str | None = Field(None, min_length=2, max_length=200, description="Updated title for the request")


class RequestFilters(BaseModel):
    status: Literal["open", "in_progress", "rejected", "closed"] | None = Field(None, description="Filter by request status")
    request_type_id: uuid.UUID | None = Field(None, description="Filter by request type")
    assigned_to_me: bool = Field(False, description="If true, return only requests where the current user has an active task assigned")
    from_date: str | None = Field(None, description="Filter requests submitted on or after this date (ISO 8601, e.g. 2024-01-01)")
    to_date: str | None = Field(None, description="Filter requests submitted on or before this date (ISO 8601, e.g. 2024-12-31)")


# --- Workflow schemas ---

class TaskDefinitionIn(BaseModel):
    key: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9_]+$", description="Unique key identifying this task within the workflow (lowercase, underscores allowed)", example="review_documents")
    name: str = Field(..., min_length=2, max_length=200, description="Human-readable name for the task", example="Review Documents")
    department_id: uuid.UUID | None = Field(None, description="ID of the department responsible for this task")
    assignee_role: str | None = Field(None, description="Role name to auto-assign this task to", example="reviewer")
    assignee_user_id: uuid.UUID | None = Field(None, description="Specific user to assign this task to — takes precedence over assignee_role")
    deadline_offset_hours: int | None = Field(None, ge=1, description="Hours from task activation until deadline", example=48)
    depends_on: list[str] = Field([], description="List of task keys that must be completed before this task activates", example=["initial_review"])
    fan_out: bool = Field(False, description="If true, creates one task instance per assignee when multiple users match the role")


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
    tasks: list[TaskDefinitionIn] = Field(..., description="Ordered list of task definitions that make up this workflow")


class WorkflowOut(BaseModel):
    id: uuid.UUID
    request_type_id: uuid.UUID
    tasks: list[TaskDefinitionOut]
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskCommentIn(BaseModel):
    body: str | None = Field(None, max_length=5000, description="Text content of the comment", example="Documents look good, proceeding to approval.")
    file_url: str | None = Field(None, description="URL of an attached file")
    file_name: str | None = Field(None, max_length=255, description="Original filename of the attachment", example="permit_docs.pdf")


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
    assigned_to_user_id: uuid.UUID | None = Field(None, description="ID of the user to assign this task to")


class TaskCompleteIn(BaseModel):
    outcome: Literal["approved", "rejected", "clarification_requested"] = Field(
        ..., description="Outcome of the task completion"
    )
    notes: str | None = Field(None, max_length=5000, description="Optional notes about the completion decision", example="All documents verified and approved.")
