from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class SignUpRequest(BaseModel):
    org_name: str
    name: str | None = None
    email: EmailStr
    password: str


class SignUpResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user: "UserOut"
    message: str


class VerifyEmailRequest(BaseModel):
    token: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserOut"


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class AcceptInviteRequest(BaseModel):
    token: str
    password: str
    name: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class SessionOut(BaseModel):
    id: str
    user_agent: str | None = None
    ip_address: str | None = None
    created_at: str
    last_used_at: str
    expires_at: str
    is_current: bool = False


# Avoid circular import by using forward reference resolved below
from app.schemas.user import UserOut  # noqa: E402

SignUpResponse.model_rebuild()
AuthResponse.model_rebuild()
