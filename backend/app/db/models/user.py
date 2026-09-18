import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OrgUser(Base):
    __tablename__ = "org_users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String, nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String, default="active", nullable=False)
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    tokens_invalidated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    org: Mapped["Organization"] = relationship("Organization", back_populates="users")
    user_roles: Mapped[list["OrgUserRole"]] = relationship(
        "OrgUserRole", back_populates="user", cascade="all, delete-orphan"
    )
    email_verification_tokens: Mapped[list["EmailVerificationToken"]] = relationship(
        "EmailVerificationToken", back_populates="user", cascade="all, delete-orphan"
    )
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        "PasswordResetToken", back_populates="user", cascade="all, delete-orphan"
    )
    invitations: Mapped[list["InvitationToken"]] = relationship(
        "InvitationToken",
        back_populates="user",
        foreign_keys="InvitationToken.user_id",
        cascade="all, delete-orphan",
    )


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("org_users.id"), nullable=False
    )
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["OrgUser"] = relationship("OrgUser", back_populates="email_verification_tokens")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("org_users.id"), nullable=False
    )
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["OrgUser"] = relationship("OrgUser", back_populates="password_reset_tokens")


class InvitationToken(Base):
    __tablename__ = "invitation_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("org_users.id"), nullable=False
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    email: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    invited_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("org_users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["OrgUser"] = relationship(
        "OrgUser", back_populates="invitations", foreign_keys=[user_id]
    )
    invited_by: Mapped["OrgUser | None"] = relationship(
        "OrgUser", foreign_keys=[invited_by_id], lazy="select"
    )
    org: Mapped["Organization"] = relationship("Organization")


class EmailChangeToken(Base):
    __tablename__ = "email_change_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("org_users.id"), nullable=False
    )
    new_email: Mapped[str] = mapped_column(String, nullable=False)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["OrgUser"] = relationship("OrgUser")
