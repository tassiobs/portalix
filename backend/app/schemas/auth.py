from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SignUpRequest(BaseModel):
    org_name: str = Field(..., min_length=2, max_length=100, description="Name of the organization to create", example="Acme Corp")
    name: str | None = Field(None, max_length=100, description="Full name of the user", example="Jane Doe")
    email: EmailStr = Field(..., description="User's email address", example="jane@acme.com")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)", example="s3cur3pass!")


class SignUpResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user: "UserOut"
    message: str


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., description="Email verification token received by email")


class AuthResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token — include as Bearer in Authorization header")
    refresh_token: str = Field(..., description="Token used to obtain a new access token when it expires")
    token_type: str = Field(default="bearer", description="Token type, always 'bearer'")
    user: "UserOut"


class SignInRequest(BaseModel):
    email: EmailStr = Field(..., description="User's email address", example="jane@acme.com")
    password: str = Field(..., description="User's password", example="s3cur3pass!")


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to send the password reset link to", example="jane@acme.com")


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Password reset token received by email")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)", example="n3wpassword!")


class AcceptInviteRequest(BaseModel):
    token: str = Field(..., description="Invitation token received by email")
    password: str = Field(..., min_length=8, description="Password to set for the new account (minimum 8 characters)", example="s3cur3pass!")
    name: str | None = Field(None, max_length=100, description="Full name of the user", example="Jane Doe")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token obtained from sign-in or refresh response")


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
