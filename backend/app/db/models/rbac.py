import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OrgRole(Base):
    __tablename__ = "org_roles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    level: Mapped[str] = mapped_column(String, nullable=False, default="org")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    org: Mapped["Organization"] = relationship("Organization", back_populates="roles")
    permissions: Mapped[list["OrgRolePermission"]] = relationship(
        "OrgRolePermission", back_populates="role", cascade="all, delete-orphan"
    )
    user_roles: Mapped[list["OrgUserRole"]] = relationship(
        "OrgUserRole", back_populates="role", cascade="all, delete-orphan"
    )


class OrgRolePermission(Base):
    __tablename__ = "org_role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("org_roles.id"), primary_key=True
    )
    permission: Mapped[str] = mapped_column(String, primary_key=True)

    role: Mapped["OrgRole"] = relationship("OrgRole", back_populates="permissions")


class OrgUserRole(Base):
    __tablename__ = "org_user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("org_users.id"), primary_key=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("org_roles.id"), primary_key=True
    )
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["OrgUser"] = relationship("OrgUser", back_populates="user_roles")
    role: Mapped["OrgRole"] = relationship("OrgRole", back_populates="user_roles")
