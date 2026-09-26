import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.portal import Portal
from app.db.models.portal_request import Request, RequestType, TaskComment, TaskDefinition, TaskInstance, Workflow
from app.db.models.rbac import OrgRole, OrgUserRole
from app.db.models.user import OrgUser
from app.schemas.portal import (
    TaskCommentIn,
    TaskCommentOut,
    TaskCompleteIn,
    TaskInstanceOut,
    TaskInstanceUpdate,
    WorkflowIn,
    WorkflowOut,
)

VALID_OUTCOMES = {"approved", "rejected", "clarification_requested"}


def _task_instance_to_out(inst: TaskInstance) -> TaskInstanceOut:
    return TaskInstanceOut(
        id=inst.id,
        request_id=inst.request_id,
        task_definition=inst.task_definition,
        status=inst.status,
        outcome=inst.outcome,
        assigned_to_user_id=inst.assigned_to_user_id,
        activated_at=inst.activated_at,
        deadline=inst.deadline,
        completed_at=inst.completed_at,
        completion_notes=inst.completion_notes,
        comments=[TaskCommentOut.model_validate(c) for c in (inst.comments or [])],
    )


def _validate_workflow_graph(tasks: list) -> None:
    keys = {t.key for t in tasks}
    for t in tasks:
        for dep in t.depends_on:
            if dep not in keys:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Task '{t.key}' depends on unknown key '{dep}'",
                )

    in_degree = {t.key: 0 for t in tasks}
    for t in tasks:
        for dep in t.depends_on:
            in_degree[t.key] += 1
    adj: dict[str, list[str]] = {t.key: [] for t in tasks}
    for t in tasks:
        for dep in t.depends_on:
            adj[dep].append(t.key)

    queue = [k for k, d in in_degree.items() if d == 0]
    visited = 0
    while queue:
        node = queue.pop()
        visited += 1
        for dep in adj[node]:
            in_degree[dep] -= 1
            if in_degree[dep] == 0:
                queue.append(dep)

    if visited != len(tasks):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Workflow tasks contain a circular dependency",
        )


async def _get_portal(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID) -> Portal:
    portal = (await db.execute(
        select(Portal).where(Portal.id == portal_id, Portal.org_id == org_id)
    )).scalar_one_or_none()
    if not portal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portal not found")
    return portal


async def _get_request_type(db: AsyncSession, portal_id: uuid.UUID, rt_id: uuid.UUID) -> RequestType:
    rt = (await db.execute(
        select(RequestType).where(RequestType.id == rt_id, RequestType.portal_id == portal_id)
    )).scalar_one_or_none()
    if not rt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request type not found")
    return rt


async def _get_request(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, request_id: uuid.UUID) -> Request:
    req = (await db.execute(
        select(Request).where(
            Request.id == request_id,
            Request.portal_id == portal_id,
        ).join(Request.portal).where(Portal.org_id == org_id)
    )).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return req


async def _get_task_instance(
    db: AsyncSession, request_id: uuid.UUID, task_id: uuid.UUID
) -> TaskInstance:
    inst = (await db.execute(
        select(TaskInstance)
        .where(TaskInstance.id == task_id, TaskInstance.request_id == request_id)
        .options(selectinload(TaskInstance.task_definition), selectinload(TaskInstance.comments))
    )).scalar_one_or_none()
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return inst


async def _spawn_fan_out_instances(
    db: AsyncSession, td: TaskDefinition, request_id: uuid.UUID, org_id: uuid.UUID, now: datetime
) -> list[TaskInstance]:
    if not td.assignee_role:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Fan-out task '{td.key}' requires an assignee_role",
        )

    users = (await db.execute(
        select(OrgUser)
        .join(OrgUserRole, OrgUser.id == OrgUserRole.user_id)
        .join(OrgRole, OrgUserRole.role_id == OrgRole.id)
        .where(OrgRole.name == td.assignee_role, OrgRole.org_id == org_id)
    )).scalars().all()

    instances = []
    for user in users:
        inst = TaskInstance(
            request_id=request_id,
            task_definition_id=td.id,
            status="active",
            assigned_to_user_id=user.id,
            activated_at=now,
            deadline=(now + timedelta(hours=td.deadline_offset_hours)) if td.deadline_offset_hours else None,
        )
        db.add(inst)
        instances.append(inst)
    return instances


async def get_workflow(db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, rt_id: uuid.UUID) -> WorkflowOut:
    await _get_portal(db, org_id, portal_id)
    await _get_request_type(db, portal_id, rt_id)

    workflow = (await db.execute(
        select(Workflow)
        .where(Workflow.request_type_id == rt_id)
        .options(selectinload(Workflow.tasks))
    )).scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No workflow configured for this request type")
    return WorkflowOut.model_validate(workflow)


async def upsert_workflow(
    db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, rt_id: uuid.UUID, data: WorkflowIn
) -> WorkflowOut:
    await _get_portal(db, org_id, portal_id)
    await _get_request_type(db, portal_id, rt_id)

    _validate_workflow_graph(data.tasks)

    existing = (await db.execute(
        select(Workflow).where(Workflow.request_type_id == rt_id)
    )).scalar_one_or_none()
    if existing:
        await db.delete(existing)
        await db.flush()

    workflow = Workflow(request_type_id=rt_id, updated_at=datetime.utcnow())
    db.add(workflow)
    await db.flush()

    for t in data.tasks:
        db.add(TaskDefinition(
            workflow_id=workflow.id,
            key=t.key,
            name=t.name,
            department_id=t.department_id,
            assignee_role=t.assignee_role,
            assignee_user_id=t.assignee_user_id,
            deadline_offset_hours=t.deadline_offset_hours,
            depends_on=t.depends_on,
            fan_out=t.fan_out,
        ))

    await db.commit()

    workflow = (await db.execute(
        select(Workflow)
        .where(Workflow.id == workflow.id)
        .options(selectinload(Workflow.tasks))
    )).scalar_one()
    return WorkflowOut.model_validate(workflow)


async def instantiate_workflow(db: AsyncSession, request_id: uuid.UUID, workflow: Workflow) -> None:
    now = datetime.utcnow()
    instances: list[TaskInstance] = []
    for td in workflow.tasks:
        if td.fan_out:
            # Fan-out tasks are spawned dynamically when their dependencies are met
            continue
        is_root = len(td.depends_on) == 0
        inst = TaskInstance(
            request_id=request_id,
            task_definition_id=td.id,
            status="active" if is_root else "waiting",
            activated_at=now if is_root else None,
            deadline=(now + timedelta(hours=td.deadline_offset_hours)) if is_root and td.deadline_offset_hours else None,
        )
        db.add(inst)
        instances.append(inst)

    if any(i.status == "active" for i in instances):
        req = (await db.execute(select(Request).where(Request.id == request_id))).scalar_one()
        req.status = "in_progress"


async def list_tasks(
    db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, request_id: uuid.UUID
) -> list[TaskInstanceOut]:
    await _get_portal(db, org_id, portal_id)
    await _get_request(db, org_id, portal_id, request_id)

    instances = (await db.execute(
        select(TaskInstance)
        .where(TaskInstance.request_id == request_id)
        .options(selectinload(TaskInstance.task_definition), selectinload(TaskInstance.comments))
    )).scalars().all()
    return [_task_instance_to_out(i) for i in instances]


async def get_task(
    db: AsyncSession, org_id: uuid.UUID, portal_id: uuid.UUID, request_id: uuid.UUID, task_id: uuid.UUID
) -> TaskInstanceOut:
    await _get_portal(db, org_id, portal_id)
    await _get_request(db, org_id, portal_id, request_id)
    inst = await _get_task_instance(db, request_id, task_id)
    return _task_instance_to_out(inst)


async def update_task(
    db: AsyncSession,
    org_id: uuid.UUID,
    portal_id: uuid.UUID,
    request_id: uuid.UUID,
    task_id: uuid.UUID,
    data: TaskInstanceUpdate,
) -> TaskInstanceOut:
    await _get_portal(db, org_id, portal_id)
    await _get_request(db, org_id, portal_id, request_id)
    inst = await _get_task_instance(db, request_id, task_id)

    if data.assigned_to_user_id is not None:
        inst.assigned_to_user_id = data.assigned_to_user_id

    await db.commit()
    await db.refresh(inst)
    return _task_instance_to_out(inst)


async def complete_task(
    db: AsyncSession,
    org_id: uuid.UUID,
    portal_id: uuid.UUID,
    request_id: uuid.UUID,
    task_id: uuid.UUID,
    data: TaskCompleteIn,
) -> TaskInstanceOut:
    if data.outcome not in VALID_OUTCOMES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"outcome must be one of: {', '.join(VALID_OUTCOMES)}",
        )

    portal = await _get_portal(db, org_id, portal_id)
    req = await _get_request(db, org_id, portal_id, request_id)
    inst = await _get_task_instance(db, request_id, task_id)

    if inst.status != "active":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Only active tasks can be completed (current status: {inst.status})",
        )

    now = datetime.utcnow()
    inst.status = "completed"
    inst.outcome = data.outcome
    inst.completed_at = now
    inst.completion_notes = data.notes
    await db.flush()

    # Reload all instances for this request
    all_instances = (await db.execute(
        select(TaskInstance)
        .where(TaskInstance.request_id == request_id)
        .options(selectinload(TaskInstance.task_definition), selectinload(TaskInstance.comments))
    )).scalars().all()

    if data.outcome == "rejected":
        for other in all_instances:
            if other.id != inst.id and other.status in ("waiting", "active"):
                other.status = "skipped"
        req.status = "rejected"

    elif data.outcome == "clarification_requested":
        req.status = "pending_clarification"

    elif data.outcome == "approved":
        # Build key → list[instances] map (fan-out tasks have multiple instances per key)
        key_to_instances: dict[str, list[TaskInstance]] = {}
        for i in all_instances:
            key = i.task_definition.key
            key_to_instances.setdefault(key, []).append(i)

        # Load all task definitions for this workflow to check fan_out flag
        workflow = (await db.execute(
            select(Workflow)
            .where(Workflow.request_type_id == req.request_type_id)
            .options(selectinload(Workflow.tasks))
        )).scalar_one_or_none()

        td_by_key: dict[str, TaskDefinition] = {}
        if workflow:
            td_by_key = {td.key: td for td in workflow.tasks}

        def _dep_satisfied(dep_key: str) -> bool:
            dep_td = td_by_key.get(dep_key)
            dep_instances = key_to_instances.get(dep_key, [])
            if dep_td and dep_td.fan_out:
                # Fan-in: ALL instances of this key must be completed+approved
                return bool(dep_instances) and all(
                    i.status == "completed" and i.outcome == "approved"
                    for i in dep_instances
                )
            # Linear: single instance must be completed+approved
            return bool(dep_instances) and dep_instances[0].status == "completed" and dep_instances[0].outcome == "approved"

        # Find waiting non-fan-out tasks ready to activate
        for other in all_instances:
            if other.status != "waiting":
                continue
            if all(_dep_satisfied(dep_key) for dep_key in other.task_definition.depends_on):
                other.status = "active"
                other.activated_at = now
                if other.task_definition.deadline_offset_hours:
                    other.deadline = now + timedelta(hours=other.task_definition.deadline_offset_hours)

        # Spawn fan-out tasks whose dependencies are now satisfied
        if workflow:
            instantiated_td_ids = {i.task_definition_id for i in all_instances}
            for td in workflow.tasks:
                if not td.fan_out:
                    continue
                if td.id in instantiated_td_ids:
                    continue
                if all(_dep_satisfied(dep_key) for dep_key in td.depends_on):
                    await _spawn_fan_out_instances(db, td, request_id, org_id, now)

        # Reload to check final state after potential fan-out spawning
        all_instances = (await db.execute(
            select(TaskInstance)
            .where(TaskInstance.request_id == request_id)
            .options(selectinload(TaskInstance.task_definition))
        )).scalars().all()

        still_pending = any(i.status in ("waiting", "active") for i in all_instances)
        if not still_pending:
            req.status = "completed"

    await db.commit()
    # Reload the completed instance with comments for the response
    inst = await _get_task_instance(db, request_id, task_id)
    return _task_instance_to_out(inst)


async def add_comment(
    db: AsyncSession,
    org_id: uuid.UUID,
    portal_id: uuid.UUID,
    request_id: uuid.UUID,
    task_id: uuid.UUID,
    current_user: OrgUser,
    data: TaskCommentIn,
) -> TaskCommentOut:
    if not data.body and not data.file_url:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A comment must have either a body or a file_url",
        )

    await _get_portal(db, org_id, portal_id)
    await _get_request(db, org_id, portal_id, request_id)
    await _get_task_instance(db, request_id, task_id)

    comment = TaskComment(
        task_instance_id=task_id,
        author_user_id=current_user.id,
        body=data.body,
        file_url=data.file_url,
        file_name=data.file_name,
        created_at=datetime.utcnow(),
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return TaskCommentOut.model_validate(comment)


async def list_comments(
    db: AsyncSession,
    org_id: uuid.UUID,
    portal_id: uuid.UUID,
    request_id: uuid.UUID,
    task_id: uuid.UUID,
) -> list[TaskCommentOut]:
    await _get_portal(db, org_id, portal_id)
    await _get_request(db, org_id, portal_id, request_id)
    await _get_task_instance(db, request_id, task_id)

    comments = (await db.execute(
        select(TaskComment)
        .where(TaskComment.task_instance_id == task_id)
        .order_by(TaskComment.created_at)
    )).scalars().all()
    return [TaskCommentOut.model_validate(c) for c in comments]
