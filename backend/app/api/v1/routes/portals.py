import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_permissions, require_portal_permissions, has_portal_permission
from app.db.models.user import OrgUser
from app.schemas.citizen import SignedUrlOut
from app.services import storage as storage_service
from app.schemas.portal import (
    AssignPortalUserRequest,
    PortalCreate,
    PortalOut,
    PortalUpdate,
    RequestTypeCreate,
    RequestTypeFieldCreate,
    RequestTypeFieldOut,
    RequestTypeFieldUpdate,
    RequestTypeOut,
    RequestTypeUpdate,
    RequestOut,
    RequestUpdate,
    RequestFilters,
    WorkflowIn,
    WorkflowOut,
    TaskInstanceOut,
    TaskInstanceUpdate,
    TaskCompleteIn,
    TaskCommentIn,
    TaskCommentOut,
)
from app.schemas.rbac import PermissionListOut
from app.services import portal as portal_service
from app.services import workflow as workflow_service
from app.services.rbac import PORTAL_PERMISSIONS

router = APIRouter(prefix="/org/portals")

_401 = {401: {"description": "Missing or invalid authentication token"}}
_403 = {403: {"description": "Insufficient permissions"}}
_404 = {404: {"description": "Resource not found"}}
_409 = {409: {"description": "Slug already in use within this org"}}


# --- Portals ---

@router.get(
    "/permissions",
    response_model=PermissionListOut,
    tags=["Portals"],
    summary="List portal-level permissions",
    description="Returns all available portal-level permission keys with labels and descriptions. "
                "Use this to populate a permissions picker when creating portal-scoped roles. "
                "Only permission keys from this list are valid for portal-level roles.",
    responses={**_401},
)
async def list_portal_permissions(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
):
    return {"data": PORTAL_PERMISSIONS}


@router.get(
    "",
    response_model=list[PortalOut],
    tags=["Portals"],
    summary="List portals",
    description="Returns all portals in the organization.",
    responses={**_401},
)
async def list_portals(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.list_portals(db, current_user.org_id)


@router.post(
    "",
    response_model=PortalOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Portals"],
    summary="Create a portal",
    description="Creates a new customer-facing portal. The slug must be unique within the org and is used in all portal URLs. "
                "If not provided it is auto-generated from the name. Requires `org.users.manage`.",
    responses={**_401, **_403, **_409},
)
async def create_portal(
    data: PortalCreate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.create_portal(db, current_user.org_id, data, current_user)


@router.patch(
    "/{portal_id}",
    response_model=PortalOut,
    tags=["Portals"],
    summary="Update a portal",
    description="Updates the portal's name, description, slug, or domain. Requires `portal.settings:manage`.",
    responses={**_401, **_403, **_404},
)
async def update_portal(
    portal_id: uuid.UUID,
    data: PortalUpdate,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.settings:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.update_portal(db, current_user.org_id, portal_id, data)


@router.delete(
    "/{portal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Portals"],
    summary="Delete a portal",
    description="Permanently deletes a portal and all associated request types, requests, and workflow data. "
                "Requires `org.users.manage`.",
    responses={**_401, **_403, **_404},
)
async def delete_portal(
    portal_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await portal_service.delete_portal(db, current_user.org_id, portal_id)


# --- Portal Users ---

@router.post(
    "/{portal_id}/users",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Portal Users"],
    summary="Assign user to portal",
    description="Assigns an org user to a portal with a specific portal-level role. "
                "The role must have `level: 'portal'`. Requires `portal.users:manage`.",
    responses={**_401, **_403, **_404, 422: {"description": "Role level mismatch — role must be portal-scoped"}},
)
async def assign_portal_user(
    portal_id: uuid.UUID,
    data: AssignPortalUserRequest,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.users:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await portal_service.assign_portal_user(db, current_user.org_id, portal_id, data)


@router.delete(
    "/{portal_id}/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Portal Users"],
    summary="Remove user from portal",
    description="Removes a user's portal-level role assignment. The user retains their org-level roles. "
                "Requires `portal.users:manage`.",
    responses={**_401, **_403, **_404},
)
async def remove_portal_user(
    portal_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.users:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await portal_service.remove_portal_user(db, current_user.org_id, portal_id, user_id)


# --- Request Types ---

@router.get(
    "/{portal_id}/request-types",
    response_model=list[RequestTypeOut],
    tags=["Request Types"],
    summary="List request types",
    description="Returns all request types defined on the portal, including their custom fields. "
                "Requires `portal.request_types:manage`.",
    responses={**_401, **_403, **_404},
)
async def list_request_types(
    portal_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.request_types:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.list_request_types(db, portal_id)


@router.post(
    "/{portal_id}/request-types",
    response_model=RequestTypeOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Request Types"],
    summary="Create a request type",
    description="Creates a new service type customers can apply for on this portal. "
                "Add fields with `POST /{portal_id}/request-types/{request_type_id}/fields`. "
                "Requires `portal.request_types:manage`.",
    responses={**_401, **_403, **_404},
)
async def create_request_type(
    portal_id: uuid.UUID,
    data: RequestTypeCreate,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.request_types:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.create_request_type(db, current_user.org_id, portal_id, data)


@router.patch(
    "/{portal_id}/request-types/{request_type_id}",
    response_model=RequestTypeOut,
    tags=["Request Types"],
    summary="Update a request type",
    description="Updates the name or description of a request type. Requires `portal.request_types:manage`.",
    responses={**_401, **_403, **_404},
)
async def update_request_type(
    portal_id: uuid.UUID,
    request_type_id: uuid.UUID,
    data: RequestTypeUpdate,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.request_types:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.update_request_type(db, current_user.org_id, portal_id, request_type_id, data)


@router.delete(
    "/{portal_id}/request-types/{request_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Request Types"],
    summary="Delete a request type",
    description="Deletes a request type and its fields. Existing customer requests of this type are not deleted. "
                "Requires `portal.request_types:manage`.",
    responses={**_401, **_403, **_404},
)
async def delete_request_type(
    portal_id: uuid.UUID,
    request_type_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.request_types:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await portal_service.delete_request_type(db, current_user.org_id, portal_id, request_type_id)


# --- Request Type Fields ---

@router.get(
    "/{portal_id}/request-types/{request_type_id}/fields",
    response_model=list[RequestTypeFieldOut],
    tags=["Request Type Fields"],
    summary="List fields",
    description="Returns all custom fields for a request type, ordered by `order`. "
                "Requires `portal.request_types:manage`.",
    responses={**_401, **_403, **_404},
)
async def list_request_type_fields(
    portal_id: uuid.UUID,
    request_type_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.request_types:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.list_request_type_fields(db, portal_id, request_type_id)


@router.post(
    "/{portal_id}/request-types/{request_type_id}/fields",
    response_model=RequestTypeFieldOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Request Type Fields"],
    summary="Add a field",
    description="Adds a custom input field to a request type. For `field_type: 'select'`, `options` is required. "
                "Requires `portal.request_types:manage`.",
    responses={**_401, **_403, **_404},
)
async def create_request_type_field(
    portal_id: uuid.UUID,
    request_type_id: uuid.UUID,
    data: RequestTypeFieldCreate,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.request_types:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.create_request_type_field(db, current_user.org_id, portal_id, request_type_id, data)


@router.patch(
    "/{portal_id}/request-types/{request_type_id}/fields/{field_id}",
    response_model=RequestTypeFieldOut,
    tags=["Request Type Fields"],
    summary="Update a field",
    description="Updates a field's label, type, options, or order. Requires `portal.request_types:manage`.",
    responses={**_401, **_403, **_404},
)
async def update_request_type_field(
    portal_id: uuid.UUID,
    request_type_id: uuid.UUID,
    field_id: uuid.UUID,
    data: RequestTypeFieldUpdate,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.request_types:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.update_request_type_field(db, current_user.org_id, portal_id, request_type_id, field_id, data)


@router.delete(
    "/{portal_id}/request-types/{request_type_id}/fields/{field_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Request Type Fields"],
    summary="Delete a field",
    description="Removes a field from the request type. Does not affect previously submitted field values. "
                "Requires `portal.request_types:manage`.",
    responses={**_401, **_403, **_404},
)
async def delete_request_type_field(
    portal_id: uuid.UUID,
    request_type_id: uuid.UUID,
    field_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.request_types:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await portal_service.delete_request_type_field(db, current_user.org_id, portal_id, request_type_id, field_id)


# --- Portal Requests (admin view) ---

@router.get(
    "/{portal_id}/requests",
    response_model=list[RequestOut],
    tags=["Portal Requests"],
    summary="List portal requests",
    description="Returns requests submitted on this portal. "
                "With `portal.requests:read` only returns requests where the caller has an assigned task. "
                "With `portal.requests:read_all` returns all requests. "
                "Supports filtering by `status`, `request_type_id`, `assigned_to_me`, `from_date`, and `to_date`.",
    responses={**_401, **_403, **_404},
)
async def list_portal_requests(
    portal_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.requests:read", "portal.requests:read_all"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    filters: Annotated[RequestFilters, Depends()],
):
    read_all = await has_portal_permission(portal_id, current_user, db, "portal.requests:read_all")
    return await portal_service.list_portal_requests(db, current_user.org_id, portal_id, current_user.id, read_all, filters)


@router.get(
    "/{portal_id}/requests/{request_id}",
    response_model=RequestOut,
    tags=["Portal Requests"],
    summary="Get a portal request",
    description="Returns a single request with its field values. "
                "Requires `portal.requests:read` (own tasks) or `portal.requests:read_all`.",
    responses={**_401, **_403, **_404},
)
async def get_portal_request(
    portal_id: uuid.UUID,
    request_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.requests:read", "portal.requests:read_all"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    read_all = await has_portal_permission(portal_id, current_user, db, "portal.requests:read_all")
    return await portal_service.get_portal_request(db, current_user.org_id, portal_id, request_id, current_user.id, read_all)


@router.patch(
    "/{portal_id}/requests/{request_id}",
    response_model=RequestOut,
    tags=["Portal Requests"],
    summary="Update a portal request",
    description="Updates the status or title of a request. Requires `portal.requests:update`.",
    responses={**_401, **_403, **_404},
)
async def update_portal_request(
    portal_id: uuid.UUID,
    request_id: uuid.UUID,
    data: RequestUpdate,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.requests:update"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.update_portal_request(db, current_user.org_id, portal_id, request_id, data)


@router.get(
    "/{portal_id}/requests/{request_id}/fields/{field_id}/signed-url",
    response_model=SignedUrlOut,
    tags=["Portal Requests"],
    summary="Get signed URL for a file field",
    description="Generates a temporary signed URL (valid 1 hour) for a `file` field on a request. "
                "Requires `portal.requests:read` or `portal.requests:read_all`.",
    responses={**_401, **_403, **_404},
)
async def get_portal_field_signed_url(
    portal_id: uuid.UUID,
    request_id: uuid.UUID,
    field_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.requests:read", "portal.requests:read_all"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    read_all = await has_portal_permission(portal_id, current_user, db, "portal.requests:read_all")
    req = await portal_service.get_portal_request(db, current_user.org_id, portal_id, request_id, current_user.id, read_all)
    fv = next((v for v in req.field_values if v.field_id == field_id), None)
    if not fv or not fv.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found or has no value")
    try:
        data = json.loads(fv.value)
        storage_path: str = data["storage_path"]
        file_name: str = data.get("file_name", "")
    except (json.JSONDecodeError, KeyError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Field value is not a valid file reference")
    signed_url = await storage_service.create_signed_url(storage_path)
    return SignedUrlOut(url=signed_url, file_name=file_name)


# --- Workflows ---

@router.get(
    "/{portal_id}/request-types/{request_type_id}/workflow",
    response_model=WorkflowOut,
    tags=["Workflows"],
    summary="Get workflow",
    description="Returns the workflow definition for a request type, including all task definitions and their dependencies. "
                "Requires `portal.workflows:view`.",
    responses={**_401, **_403, **_404},
)
async def get_workflow(
    portal_id: uuid.UUID,
    request_type_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.workflows:view"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await workflow_service.get_workflow(db, current_user.org_id, portal_id, request_type_id)


@router.put(
    "/{portal_id}/request-types/{request_type_id}/workflow",
    response_model=WorkflowOut,
    tags=["Workflows"],
    summary="Create or replace workflow",
    description="Replaces the entire workflow for a request type. This is a full replacement — send all task definitions "
                "you want to keep. Task `key` values must be unique within the workflow. Requires `portal.workflows:manage`.",
    responses={**_401, **_403, **_404},
)
async def upsert_workflow(
    portal_id: uuid.UUID,
    request_type_id: uuid.UUID,
    data: WorkflowIn,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.workflows:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await workflow_service.upsert_workflow(db, current_user.org_id, portal_id, request_type_id, data)


# --- Tasks ---

@router.get(
    "/{portal_id}/requests/{request_id}/tasks",
    response_model=list[TaskInstanceOut],
    tags=["Tasks"],
    summary="List task instances",
    description="Returns all workflow task instances for a request, including their status, assignee, and comments. "
                "Requires `portal.requests:read`.",
    responses={**_401, **_403, **_404},
)
async def list_tasks(
    portal_id: uuid.UUID,
    request_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.requests:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await workflow_service.list_tasks(db, current_user.org_id, portal_id, request_id)


@router.get(
    "/{portal_id}/requests/{request_id}/tasks/{task_id}",
    response_model=TaskInstanceOut,
    tags=["Tasks"],
    summary="Get a task instance",
    description="Returns a single task instance with its definition, status, and comments. "
                "Requires `portal.requests:read`.",
    responses={**_401, **_403, **_404},
)
async def get_task(
    portal_id: uuid.UUID,
    request_id: uuid.UUID,
    task_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.requests:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await workflow_service.get_task(db, current_user.org_id, portal_id, request_id, task_id)


@router.patch(
    "/{portal_id}/requests/{request_id}/tasks/{task_id}",
    response_model=TaskInstanceOut,
    tags=["Tasks"],
    summary="Update a task instance",
    description="Updates the assignee of a task instance. Requires `portal.requests:update`.",
    responses={**_401, **_403, **_404},
)
async def update_task(
    portal_id: uuid.UUID,
    request_id: uuid.UUID,
    task_id: uuid.UUID,
    data: TaskInstanceUpdate,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.requests:update"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await workflow_service.update_task(db, current_user.org_id, portal_id, request_id, task_id, data)


@router.post(
    "/{portal_id}/requests/{request_id}/tasks/{task_id}/complete",
    response_model=TaskInstanceOut,
    tags=["Tasks"],
    summary="Complete a task instance",
    description="Marks a task as complete with an outcome (`approved`, `rejected`, or `clarification_requested`). "
                "Completing a task may activate downstream tasks in the workflow. Requires `portal.requests:update`.",
    responses={**_401, **_403, **_404},
)
async def complete_task(
    portal_id: uuid.UUID,
    request_id: uuid.UUID,
    task_id: uuid.UUID,
    data: TaskCompleteIn,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.requests:update"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await workflow_service.complete_task(db, current_user.org_id, portal_id, request_id, task_id, data)


# --- Task Comments ---

@router.post(
    "/{portal_id}/requests/{request_id}/tasks/{task_id}/comments",
    response_model=TaskCommentOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Task Comments"],
    summary="Add a comment",
    description="Adds a comment to a task instance. At least one of `body` or `file_url` must be provided. "
                "Requires `portal.requests:update`.",
    responses={**_401, **_403, **_404},
)
async def add_task_comment(
    portal_id: uuid.UUID,
    request_id: uuid.UUID,
    task_id: uuid.UUID,
    data: TaskCommentIn,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.requests:update"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await workflow_service.add_comment(db, current_user.org_id, portal_id, request_id, task_id, current_user, data)


@router.get(
    "/{portal_id}/requests/{request_id}/tasks/{task_id}/comments",
    response_model=list[TaskCommentOut],
    tags=["Task Comments"],
    summary="List comments",
    description="Returns all comments on a task instance, ordered by creation time. "
                "Requires `portal.requests:read`.",
    responses={**_401, **_403, **_404},
)
async def list_task_comments(
    portal_id: uuid.UUID,
    request_id: uuid.UUID,
    task_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.requests:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await workflow_service.list_comments(db, current_user.org_id, portal_id, request_id, task_id)
