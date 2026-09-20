import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
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
