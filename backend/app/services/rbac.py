import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.rbac import OrgRole, OrgRolePermission, OrgUserRole
from app.db.models.user import OrgUser
from app.schemas.rbac import RoleCreate, RoleOut, RoleUpdate

ORG_PERMISSIONS = [
    {
        "key": "org.users.manage",
        "label": "Manage Users",
        "description": "Add/update/deactivate org users; assign org roles",
        "level": "org",
    },
    {
        "key": "org.portals.manage",
        "label": "Manage Portals",
        "description": "Create/update/archive portals",
        "level": "org",
    },
    {
        "key": "requests:read",
        "label": "View Requests",
        "description": "View requests in the organization",
        "level": "org",
    },
    {
        "key": "requests:create",
        "label": "Create Requests",
        "description": "Create new requests in the organization",
        "level": "org",
    },
    {
        "key": "requests:update",
        "label": "Update Requests",
        "description": "Update title or status of existing requests",
        "level": "org",
    },
    {
        "key": "requests:delete",
        "label": "Delete Requests",
        "description": "Delete requests from the organization",
        "level": "org",
    },
]

VALID_PERMISSION_KEYS = {p["key"] for p in ORG_PERMISSIONS}


def build_role_out(role: OrgRole) -> RoleOut:
    perms = [rp.permission for rp in role.permissions] if role.permissions else []
    return RoleOut(
        id=role.id,
        name=role.name,
        description=role.description,
        level="org",
        permissions=perms,
        is_default=role.is_default,
        created_at=role.created_at,
    )


async def list_roles(db: AsyncSession, org_id: uuid.UUID) -> list[RoleOut]:
    result = await db.execute(
        select(OrgRole)
        .where(OrgRole.org_id == org_id)
        .options(selectinload(OrgRole.permissions))
        .order_by(OrgRole.created_at)
    )
    roles = result.scalars().all()
    return [build_role_out(r) for r in roles]


async def create_role(db: AsyncSession, org_id: uuid.UUID, data: RoleCreate) -> RoleOut:
    invalid = set(data.permissions) - VALID_PERMISSION_KEYS
    if invalid:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid permissions: {invalid}")

    role = OrgRole(org_id=org_id, name=data.name, description=data.description)
    db.add(role)
    await db.flush()

    for perm_key in data.permissions:
        db.add(OrgRolePermission(role_id=role.id, permission=perm_key))

    await db.commit()
    await db.refresh(role)

    result = await db.execute(
        select(OrgRole).where(OrgRole.id == role.id).options(selectinload(OrgRole.permissions))
    )
    role = result.scalar_one()
    return build_role_out(role)


async def get_role(db: AsyncSession, org_id: uuid.UUID, role_id: uuid.UUID) -> RoleOut:
    result = await db.execute(
        select(OrgRole)
        .where(OrgRole.id == role_id, OrgRole.org_id == org_id)
        .options(selectinload(OrgRole.permissions))
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return build_role_out(role)


async def update_role(db: AsyncSession, org_id: uuid.UUID, role_id: uuid.UUID, data: RoleUpdate) -> RoleOut:
    result = await db.execute(
        select(OrgRole)
        .where(OrgRole.id == role_id, OrgRole.org_id == org_id)
        .options(selectinload(OrgRole.permissions))
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    if data.name is not None:
        role.name = data.name
    if data.description is not None:
        role.description = data.description

    if data.permissions is not None:
        invalid = set(data.permissions) - VALID_PERMISSION_KEYS
        if invalid:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid permissions: {invalid}")

        # Replace permissions
        for perm in list(role.permissions):
            await db.delete(perm)
        await db.flush()

        for perm_key in data.permissions:
            db.add(OrgRolePermission(role_id=role.id, permission=perm_key))

    await db.commit()

    result = await db.execute(
        select(OrgRole).where(OrgRole.id == role.id).options(selectinload(OrgRole.permissions))
    )
    role = result.scalar_one()
    return build_role_out(role)


async def delete_role(db: AsyncSession, org_id: uuid.UUID, role_id: uuid.UUID) -> None:
    result = await db.execute(
        select(OrgRole).where(OrgRole.id == role_id, OrgRole.org_id == org_id)
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    if role.is_default:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot delete a default role")

    await db.delete(role)
    await db.commit()


async def list_user_roles(db: AsyncSession, user_id: uuid.UUID) -> list[RoleOut]:
    result = await db.execute(
        select(OrgUserRole)
        .where(OrgUserRole.user_id == user_id)
        .options(selectinload(OrgUserRole.role).selectinload(OrgRole.permissions))
    )
    user_roles = result.scalars().all()
    return [build_role_out(ur.role) for ur in user_roles]


async def assign_role(
    db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID, role_id: uuid.UUID
) -> None:
    # Verify role belongs to org
    role_result = await db.execute(
        select(OrgRole).where(OrgRole.id == role_id, OrgRole.org_id == org_id)
    )
    if not role_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    # Check not already assigned
    existing = await db.execute(
        select(OrgUserRole).where(
            OrgUserRole.user_id == user_id, OrgUserRole.role_id == role_id
        )
    )
    if existing.scalar_one_or_none():
        return  # Already assigned, idempotent

    db.add(OrgUserRole(user_id=user_id, role_id=role_id))
    await db.commit()


async def remove_role(
    db: AsyncSession, user_id: uuid.UUID, role_id: uuid.UUID
) -> None:
    result = await db.execute(
        select(OrgUserRole).where(
            OrgUserRole.user_id == user_id, OrgUserRole.role_id == role_id
        )
    )
    ur = result.scalar_one_or_none()
    if not ur:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role assignment not found")

    await db.delete(ur)
    await db.commit()
