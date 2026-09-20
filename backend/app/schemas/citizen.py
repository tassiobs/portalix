import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class CitizenSignUpRequest(BaseModel):
    name: str | None = None
    email: EmailStr
    password: str


class CitizenSignInRequest(BaseModel):
    email: EmailStr
    password: str


class CitizenVerifyEmailRequest(BaseModel):
    token: str


class CitizenForgotPasswordRequest(BaseModel):
    email: EmailStr


class CitizenResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class CitizenRefreshRequest(BaseModel):
    refresh_token: str


class CitizenOut(BaseModel):
    id: uuid.UUID
    portal_id: uuid.UUID
    name: str | None
    email: str
    email_verified: bool
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CitizenAuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    citizen: CitizenOut


class CitizenSignUpResponse(BaseModel):
    citizen: CitizenOut
    message: str
    verification_token: str


class CitizenRequestCreate(BaseModel):
    request_type_id: uuid.UUID
    title: str


class CitizenRequestOut(BaseModel):
    id: uuid.UUID
    portal_id: uuid.UUID
    request_type_id: uuid.UUID
    citizen_id: uuid.UUID
    title: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
