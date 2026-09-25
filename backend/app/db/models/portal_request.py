import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
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


class RequestFieldValue(Base):
    __tablename__ = "request_field_values"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("requests.id"), nullable=False)
    field_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("request_type_fields.id"), nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)

    request: Mapped["Request"] = relationship("Request", back_populates="field_values")
    field: Mapped["RequestTypeField"] = relationship("RequestTypeField")
