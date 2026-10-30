import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_permissions, require_portal_permissions, has_portal_permission
from app.db.models.user import OrgUser
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
    WorkflowIn,
    WorkflowOut,
    TaskInstanceOut,
    TaskInstanceUpdate,
    TaskCompleteIn,
    TaskCommentIn,
    TaskCommentOut,
)
from app.services import portal as portal_service
from app.services import workflow as workflow_service
from app.services.rbac import PORTAL_PERMISSIONS

router = APIRouter(prefix="/org/portals")


@router.get("/permissions", tags=["Portals"])
async def list_portal_permissions(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
):
    return {"data": PORTAL_PERMISSIONS}


@router.get("", response_model=list[PortalOut], tags=["Portals"])
async def list_portals(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.list_portals(db, current_user.org_id)


@router.post("", response_model=PortalOut, status_code=status.HTTP_201_CREATED, tags=["Portals"])
async def create_portal(
    data: PortalCreate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.create_portal(db, current_user.org_id, data, current_user)


@router.patch("/{portal_id}", response_model=PortalOut, tags=["Portals"])
async def update_portal(
    portal_id: uuid.UUID,
    data: PortalUpdate,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.settings:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.update_portal(db, current_user.org_id, portal_id, data)


@router.delete("/{portal_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Portals"])
async def delete_portal(
    portal_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await portal_service.delete_portal(db, current_user.org_id, portal_id)


# --- Portal Users ---

@router.post("/{portal_id}/users", status_code=status.HTTP_204_NO_CONTENT, tags=["Portal Users"])
async def assign_portal_user(
    portal_id: uuid.UUID,
    data: AssignPortalUserRequest,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.users:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await portal_service.assign_portal_user(db, current_user.org_id, portal_id, data)


@router.delete("/{portal_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Portal Users"])
async def remove_portal_user(
    portal_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.users:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await portal_service.remove_portal_user(db, current_user.org_id, portal_id, user_id)


# --- Request Types ---

@router.get("/{portal_id}/request-types", response_model=list[RequestTypeOut], tags=["Request Types"])
async def list_request_types(
    portal_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.request_types:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.list_request_types(db, portal_id)


@router.post("/{portal_id}/request-types", response_model=RequestTypeOut, status_code=status.HTTP_201_CREATED, tags=["Request Types"])
async def create_request_type(
    portal_id: uuid.UUID,
    data: RequestTypeCreate,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.request_types:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.create_request_type(db, current_user.org_id, portal_id, data)


@router.patch("/{portal_id}/request-types/{rt_id}", response_model=RequestTypeOut, tags=["Request Types"])
async def update_request_type(
    portal_id: uuid.UUID,
    rt_id: uuid.UUID,
    data: RequestTypeUpdate,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.request_types:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.update_request_type(db, current_user.org_id, portal_id, rt_id, data)


@router.delete("/{portal_id}/request-types/{rt_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Request Types"])
async def delete_request_type(
    portal_id: uuid.UUID,
    rt_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.request_types:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await portal_service.delete_request_type(db, current_user.org_id, portal_id, rt_id)


# --- Request Type Fields ---

@router.get("/{portal_id}/request-types/{rt_id}/fields", response_model=list[RequestTypeFieldOut], tags=["Request Type Fields"])
async def list_request_type_fields(
    portal_id: uuid.UUID,
    rt_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.request_types:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.list_request_type_fields(db, portal_id, rt_id)


@router.post("/{portal_id}/request-types/{rt_id}/fields", response_model=RequestTypeFieldOut, status_code=status.HTTP_201_CREATED, tags=["Request Type Fields"])
async def create_request_type_field(
    portal_id: uuid.UUID,
    rt_id: uuid.UUID,
    data: RequestTypeFieldCreate,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.request_types:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.create_request_type_field(db, current_user.org_id, portal_id, rt_id, data)


@router.patch("/{portal_id}/request-types/{rt_id}/fields/{field_id}", response_model=RequestTypeFieldOut, tags=["Request Type Fields"])
async def update_request_type_field(
    portal_id: uuid.UUID,
    rt_id: uuid.UUID,
    field_id: uuid.UUID,
    data: RequestTypeFieldUpdate,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.request_types:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.update_request_type_field(db, current_user.org_id, portal_id, rt_id, field_id, data)


@router.delete("/{portal_id}/request-types/{rt_id}/fields/{field_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Request Type Fields"])
async def delete_request_type_field(
    portal_id: uuid.UUID,
    rt_id: uuid.UUID,
    field_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.request_types:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await portal_service.delete_request_type_field(db, current_user.org_id, portal_id, rt_id, field_id)


# --- Portal Requests (admin view) ---

@router.get("/{portal_id}/requests", response_model=list[RequestOut], tags=["Portal Requests"])
async def list_portal_requests(
    portal_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.requests:read", "portal.requests:read_all"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    read_all = await has_portal_permission(portal_id, current_user, db, "portal.requests:read_all")
    return await portal_service.list_portal_requests(db, current_user.org_id, portal_id, current_user.id, read_all)


@router.get("/{portal_id}/requests/{request_id}", response_model=RequestOut, tags=["Portal Requests"])
async def get_portal_request(
    portal_id: uuid.UUID,
    request_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.requests:read", "portal.requests:read_all"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    read_all = await has_portal_permission(portal_id, current_user, db, "portal.requests:read_all")
    return await portal_service.get_portal_request(db, current_user.org_id, portal_id, request_id, current_user.id, read_all)


@router.patch("/{portal_id}/requests/{request_id}", response_model=RequestOut, tags=["Portal Requests"])
async def update_portal_request(
    portal_id: uuid.UUID,
    request_id: uuid.UUID,
    data: RequestUpdate,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.requests:update"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await portal_service.update_portal_request(db, current_user.org_id, portal_id, request_id, data)


# --- Workflows ---

@router.get("/{portal_id}/request-types/{rt_id}/workflow", response_model=WorkflowOut, tags=["Workflows"])
async def get_workflow(
    portal_id: uuid.UUID,
    rt_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.workflows:view"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await workflow_service.get_workflow(db, current_user.org_id, portal_id, rt_id)


@router.put("/{portal_id}/request-types/{rt_id}/workflow", response_model=WorkflowOut, tags=["Workflows"])
async def upsert_workflow(
    portal_id: uuid.UUID,
    rt_id: uuid.UUID,
    data: WorkflowIn,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.workflows:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await workflow_service.upsert_workflow(db, current_user.org_id, portal_id, rt_id, data)


# --- Tasks ---

@router.get("/{portal_id}/requests/{request_id}/tasks", response_model=list[TaskInstanceOut], tags=["Tasks"])
async def list_tasks(
    portal_id: uuid.UUID,
    request_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.requests:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await workflow_service.list_tasks(db, current_user.org_id, portal_id, request_id)


@router.get("/{portal_id}/requests/{request_id}/tasks/{task_id}", response_model=TaskInstanceOut, tags=["Tasks"])
async def get_task(
    portal_id: uuid.UUID,
    request_id: uuid.UUID,
    task_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.requests:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await workflow_service.get_task(db, current_user.org_id, portal_id, request_id, task_id)


@router.patch("/{portal_id}/requests/{request_id}/tasks/{task_id}", response_model=TaskInstanceOut, tags=["Tasks"])
async def update_task(
    portal_id: uuid.UUID,
    request_id: uuid.UUID,
    task_id: uuid.UUID,
    data: TaskInstanceUpdate,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.requests:update"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await workflow_service.update_task(db, current_user.org_id, portal_id, request_id, task_id, data)


@router.post("/{portal_id}/requests/{request_id}/tasks/{task_id}/complete", response_model=TaskInstanceOut, tags=["Tasks"])
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


@router.get("/{portal_id}/requests/{request_id}/tasks/{task_id}/comments", response_model=list[TaskCommentOut], tags=["Task Comments"])
async def list_task_comments(
    portal_id: uuid.UUID,
    request_id: uuid.UUID,
    task_id: uuid.UUID,
    current_user: Annotated[OrgUser, Depends(require_portal_permissions("portal.requests:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await workflow_service.list_comments(db, current_user.org_id, portal_id, request_id, task_id)
