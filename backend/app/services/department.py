import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.department import Department, DepartmentMember
from app.db.models.user import OrgUser
from app.schemas.department import AddMemberRequest, DepartmentCreate, DepartmentDetailOut, DepartmentOut, DepartmentUpdate


async def _get_department(db: AsyncSession, org_id: uuid.UUID, department_id: uuid.UUID) -> Department:
    dept = (await db.execute(
        select(Department).where(Department.id == department_id, Department.org_id == org_id)
    )).scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return dept


def _to_out(dept: Department, member_count: int) -> DepartmentOut:
    return DepartmentOut(
        id=dept.id,
        org_id=dept.org_id,
        name=dept.name,
        description=dept.description,
        member_count=member_count,
        created_at=dept.created_at,
    )


async def list_departments(db: AsyncSession, org_id: uuid.UUID) -> list[DepartmentOut]:
    rows = (await db.execute(
        select(Department, func.count(DepartmentMember.id).label("member_count"))
        .outerjoin(DepartmentMember, DepartmentMember.department_id == Department.id)
        .where(Department.org_id == org_id)
        .group_by(Department.id)
        .order_by(Department.name)
    )).all()
    return [_to_out(dept, count) for dept, count in rows]


async def create_department(db: AsyncSession, org_id: uuid.UUID, data: DepartmentCreate) -> DepartmentOut:
    dept = Department(org_id=org_id, name=data.name, description=data.description)
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return _to_out(dept, 0)


async def get_department(db: AsyncSession, org_id: uuid.UUID, department_id: uuid.UUID) -> DepartmentDetailOut:
    dept = (await db.execute(
        select(Department)
        .where(Department.id == department_id, Department.org_id == org_id)
        .options(selectinload(Department.members).selectinload(DepartmentMember.user))
    )).scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return DepartmentDetailOut(
        id=dept.id,
        org_id=dept.org_id,
        name=dept.name,
        description=dept.description,
        member_count=len(dept.members),
        created_at=dept.created_at,
        members=dept.members,
    )


async def update_department(db: AsyncSession, org_id: uuid.UUID, department_id: uuid.UUID, data: DepartmentUpdate) -> DepartmentOut:
    dept = await _get_department(db, org_id, department_id)
    if data.name is not None:
        dept.name = data.name
    if data.description is not None:
        dept.description = data.description
    await db.commit()
    count = (await db.execute(
        select(func.count(DepartmentMember.id)).where(DepartmentMember.department_id == dept.id)
    )).scalar_one()
    return _to_out(dept, count)


async def delete_department(db: AsyncSession, org_id: uuid.UUID, department_id: uuid.UUID) -> None:
    dept = await _get_department(db, org_id, department_id)
    await db.delete(dept)
    await db.commit()


async def add_member(db: AsyncSession, org_id: uuid.UUID, department_id: uuid.UUID, data: AddMemberRequest) -> None:
    await _get_department(db, org_id, department_id)

    user = (await db.execute(
        select(OrgUser).where(OrgUser.id == data.user_id, OrgUser.org_id == org_id)
    )).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing = (await db.execute(
        select(DepartmentMember).where(
            DepartmentMember.department_id == department_id,
            DepartmentMember.user_id == data.user_id,
        )
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a member of this department")

    db.add(DepartmentMember(department_id=department_id, user_id=data.user_id))
    await db.commit()


async def remove_member(db: AsyncSession, org_id: uuid.UUID, department_id: uuid.UUID, user_id: uuid.UUID) -> None:
    await _get_department(db, org_id, department_id)
    member = (await db.execute(
        select(DepartmentMember).where(
            DepartmentMember.department_id == department_id,
            DepartmentMember.user_id == user_id,
        )
    )).scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User is not a member of this department")
    await db.delete(member)
    await db.commit()


async def list_user_departments(db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID) -> list[DepartmentOut]:
    member_subq = select(DepartmentMember.department_id).where(DepartmentMember.user_id == user_id).scalar_subquery()
    rows = (await db.execute(
        select(Department, func.count(DepartmentMember.id).label("member_count"))
        .outerjoin(DepartmentMember, DepartmentMember.department_id == Department.id)
        .where(Department.org_id == org_id, Department.id.in_(member_subq))
        .group_by(Department.id)
        .order_by(Department.name)
    )).all()
    return [_to_out(dept, count) for dept, count in rows]
