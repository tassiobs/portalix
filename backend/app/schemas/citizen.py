import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class CitizenSignUpRequest(BaseModel):
    name: str | None = Field(None, max_length=100, description="Full name of the citizen", example="John Smith")
    email: EmailStr = Field(..., description="Citizen's email address", example="john@example.com")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)", example="s3cur3pass!")
    redirect_url: str | None = Field(None, description="Base URL for the verification email link (e.g. https://your-app.com/portal/{org_slug}/{portal_slug}/auth/verify-email). Falls back to the server default if omitted.", example="https://your-app.com/portal/springfield/permits/auth/verify-email")


class CitizenSignInRequest(BaseModel):
    email: EmailStr = Field(..., description="Citizen's email address", example="john@example.com")
    password: str = Field(..., description="Citizen's password", example="s3cur3pass!")


class CitizenVerifyEmailRequest(BaseModel):
    token: str = Field(..., description="Email verification token received by email")


class CitizenForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to send the password reset link to", example="john@example.com")


class CitizenResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Password reset token received by email")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)", example="n3wpassword!")


class CitizenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token obtained from sign-in or refresh response")


class CitizenExchangeRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token from any portal in the same org")


class CitizenOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    name: str | None
    email: str
    email_verified: bool
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CitizenAuthResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token — include as Bearer in Authorization header")
    refresh_token: str = Field(..., description="Token used to obtain a new access token when it expires")
    token_type: str = Field(default="bearer", description="Token type, always 'bearer'")
    citizen: CitizenOut


class CitizenSignUpResponse(BaseModel):
    citizen: CitizenOut
    message: str


class CitizenFieldValueSubmit(BaseModel):
    field_id: uuid.UUID = Field(..., description="ID of the request type field being answered")
    value: str | None = Field(None, max_length=5000, description="Value submitted for this field")


class CitizenRequestCreate(BaseModel):
    request_type_id: uuid.UUID = Field(..., description="ID of the request type to submit")
    title: str = Field(..., min_length=2, max_length=200, description="Short descriptive title for the request", example="Permit for home renovation")
    field_values: list[CitizenFieldValueSubmit] = Field([], description="Values for the request type's custom fields")


class UploadOut(BaseModel):
    storage_path: str = Field(..., description="Opaque storage path — pass as field value when submitting the request")
    file_name: str = Field(..., description="Original filename")


class SignedUrlOut(BaseModel):
    url: str = Field(..., description="Temporary signed URL valid for 1 hour")
    file_name: str = Field(..., description="Original filename")


class CitizenRequestOut(BaseModel):
    id: uuid.UUID
    portal_id: uuid.UUID
    request_type_id: uuid.UUID
    request_type_name: str | None = None
    citizen_id: uuid.UUID
    title: str
    status: str
    field_values: list = []
    created_at: datetime

    model_config = {"from_attributes": True}
