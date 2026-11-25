from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_permissions
from app.db.models.user import OrgUser
from app.schemas.department import AddMemberRequest, DepartmentCreate, DepartmentDetailOut, DepartmentOut, DepartmentUpdate
from app.services import department as department_service

router = APIRouter(prefix="/org/departments", tags=["Org Departments"])

_401 = {401: {"description": "Missing or invalid authentication token"}}
_403 = {403: {"description": "Requires `org.departments.manage` permission"}}
_404 = {404: {"description": "Department not found"}}


@router.get(
    "",
    response_model=list[DepartmentOut],
    summary="List departments",
    description="Returns all departments in the organization with their member count.",
    responses={**_401},
)
async def list_departments(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await department_service.list_departments(db, current_user.org_id)


@router.post(
    "",
    response_model=DepartmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a department",
    description="Creates a new department in the organization. Requires `org.departments.manage`.",
    responses={**_401, **_403},
)
async def create_department(
    data: DepartmentCreate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.departments.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await department_service.create_department(db, current_user.org_id, data)


@router.get(
    "/{department_id}",
    response_model=DepartmentDetailOut,
    summary="Get a department",
    description="Returns a department with its full member list.",
    responses={**_401, **_404},
)
async def get_department(
    department_id: UUID,
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await department_service.get_department(db, current_user.org_id, department_id)


@router.patch(
    "/{department_id}",
    response_model=DepartmentOut,
    summary="Update a department",
    description="Updates a department's name or description. Requires `org.departments.manage`.",
    responses={**_401, **_403, **_404},
)
async def update_department(
    department_id: UUID,
    data: DepartmentUpdate,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.departments.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await department_service.update_department(db, current_user.org_id, department_id, data)


@router.delete(
    "/{department_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a department",
    description="Deletes a department and removes all its members. Requires `org.departments.manage`.",
    responses={**_401, **_403, **_404},
)
async def delete_department(
    department_id: UUID,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.departments.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await department_service.delete_department(db, current_user.org_id, department_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{department_id}/members",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Add a member",
    description="Adds an org user to the department. Requires `org.departments.manage`.",
    responses={**_401, **_403, **_404, 409: {"description": "User is already a member of this department"}},
)
async def add_member(
    department_id: UUID,
    data: AddMemberRequest,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.departments.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await department_service.add_member(db, current_user.org_id, department_id, data)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{department_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member",
    description="Removes a user from the department. Requires `org.departments.manage`.",
    responses={**_401, **_403, **_404},
)
async def remove_member(
    department_id: UUID,
    user_id: UUID,
    current_user: Annotated[OrgUser, Depends(require_permissions("org.departments.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await department_service.remove_member(db, current_user.org_id, department_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
