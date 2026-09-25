import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Portal(Base):
    __tablename__ = "portals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    domain: Mapped[str | None] = mapped_column(String, unique=True, nullable=True, index=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("org_users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("org_id", "slug", name="uq_portal_org_slug"),)

    org: Mapped["Organization"] = relationship("Organization", back_populates="portals")
    created_by: Mapped["OrgUser | None"] = relationship("OrgUser", foreign_keys=[created_by_id])
    user_roles: Mapped[list["PortalUserRole"]] = relationship("PortalUserRole", back_populates="portal", cascade="all, delete-orphan")
    request_types: Mapped[list["RequestType"]] = relationship("RequestType", back_populates="portal", cascade="all, delete-orphan")
    requests: Mapped[list["Request"]] = relationship("Request", back_populates="portal", cascade="all, delete-orphan")



class PortalUserRole(Base):
    __tablename__ = "portal_user_roles"

    portal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("portals.id"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("org_users.id"), primary_key=True)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("org_roles.id"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    portal: Mapped["Portal"] = relationship("Portal", back_populates="user_roles")
    user: Mapped["OrgUser"] = relationship("OrgUser")
    role: Mapped["OrgRole"] = relationship("OrgRole")
