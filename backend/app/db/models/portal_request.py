import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RequestType(Base):
    __tablename__ = "request_types"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("portals.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    portal: Mapped["Portal"] = relationship("Portal", back_populates="request_types")
    requests: Mapped[list["Request"]] = relationship("Request", back_populates="request_type")
    fields: Mapped[list["RequestTypeField"]] = relationship(
        "RequestTypeField", back_populates="request_type", cascade="all, delete-orphan", order_by="RequestTypeField.order"
    )
    workflow: Mapped["Workflow | None"] = relationship("Workflow", back_populates="request_type", uselist=False)


class RequestTypeField(Base):
    __tablename__ = "request_type_fields"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("request_types.id"), nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    field_type: Mapped[str] = mapped_column(String, nullable=False)  # text, textarea, number, date, select
    required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)  # for select fields
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    request_type: Mapped["RequestType"] = relationship("RequestType", back_populates="fields")


class Request(Base):
    __tablename__ = "requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("portals.id"), nullable=False)
    request_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("request_types.id"), nullable=False)
    citizen_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("citizens.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    portal: Mapped["Portal"] = relationship("Portal", back_populates="requests")
    request_type: Mapped["RequestType"] = relationship("RequestType", back_populates="requests")
    citizen: Mapped["Citizen"] = relationship("Citizen")
    field_values: Mapped[list["RequestFieldValue"]] = relationship(
        "RequestFieldValue", back_populates="request", cascade="all, delete-orphan"
    )
    task_instances: Mapped[list["TaskInstance"]] = relationship(
        "TaskInstance", back_populates="request", cascade="all, delete-orphan"
    )


class RequestFieldValue(Base):
    __tablename__ = "request_field_values"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("requests.id"), nullable=False)
    field_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("request_type_fields.id"), nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)

    request: Mapped["Request"] = relationship("Request", back_populates="field_values")
    field: Mapped["RequestTypeField"] = relationship("RequestTypeField")


class Workflow(Base):
    __tablename__ = "workflows"
    __table_args__ = (UniqueConstraint("request_type_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("request_types.id"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    request_type: Mapped["RequestType"] = relationship("RequestType", back_populates="workflow")
    tasks: Mapped[list["TaskDefinition"]] = relationship(
        "TaskDefinition", back_populates="workflow", cascade="all, delete-orphan"
    )


class TaskDefinition(Base):
    __tablename__ = "task_definitions"
    __table_args__ = (UniqueConstraint("workflow_id", "key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    key: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    assignee_role: Mapped[str | None] = mapped_column(String, nullable=True)
    assignee_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("org_users.id"), nullable=True)
    deadline_offset_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    depends_on: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)

    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="tasks")
    instances: Mapped[list["TaskInstance"]] = relationship("TaskInstance", back_populates="task_definition")


class TaskInstance(Base):
    __tablename__ = "task_instances"
    __table_args__ = (Index("ix_task_instances_request_id", "request_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("requests.id"), nullable=False)
    task_definition_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("task_definitions.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, default="waiting", nullable=False)
    outcome: Mapped[str | None] = mapped_column(String, nullable=True)
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("org_users.id"), nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completion_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    request: Mapped["Request"] = relationship("Request", back_populates="task_instances")
    task_definition: Mapped["TaskDefinition"] = relationship("TaskDefinition", back_populates="instances")
