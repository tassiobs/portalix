import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    settings: Mapped["OrgSettings"] = relationship("OrgSettings", back_populates="org", uselist=False)
    users: Mapped[list] = relationship("OrgUser", back_populates="org")
    roles: Mapped[list] = relationship("OrgRole", back_populates="org")


class OrgSettings(Base):
    __tablename__ = "org_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), unique=True, nullable=False
    )
    citizen_identity_scope: Mapped[str] = mapped_column(String, default="portal", nullable=False)
    lockout_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    lockout_max_attempts: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    lockout_duration_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("org_users.id"), nullable=True
    )

    org: Mapped["Organization"] = relationship("Organization", back_populates="settings")
    updated_by: Mapped["OrgUser | None"] = relationship(
        "OrgUser", foreign_keys=[updated_by_id], lazy="select"
    )
