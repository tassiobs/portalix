from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Header, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, get_redis
from app.db.models.user import OrgUser
from app.schemas.auth import (
    AcceptInviteRequest,
    AuthResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    RefreshRequest,
    ResetPasswordRequest,
    SignInRequest,
    SignUpRequest,
    SignUpResponse,
    VerifyEmailRequest,
)
from app.schemas.user import OrgUserUpdate, UserOut
from app.services import auth as auth_service
from app.services import user as user_service

router = APIRouter(prefix="/auth", tags=["Auth"])


def _get_client_info(request: Request) -> tuple[str | None, str | None]:
    user_agent = request.headers.get("user-agent")
    ip = request.client.host if request.client else None
    return user_agent, ip


@router.post("/sign-up", response_model=SignUpResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(
    data: SignUpRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    return await auth_service.sign_up(db, redis, data)


@router.post("/verify-email")
async def verify_email(
    data: VerifyEmailRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await auth_service.verify_email(db, data.token)


@router.post("/resend-verification")
async def resend_verification(
    body: ForgotPasswordRequest,  # reuse email field
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await auth_service.resend_verification(db, body.email)


@router.post("/sign-in", response_model=AuthResponse)
async def sign_in(
    data: SignInRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    user_agent, ip = _get_client_info(request)
    return await auth_service.sign_in(db, redis, data.email, data.password, user_agent, ip)


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    data: RefreshRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    user_agent, ip = _get_client_info(request)
    return await auth_service.refresh_tokens(db, redis, data.refresh_token, user_agent, ip)


@router.post("/sign-out", status_code=status.HTTP_204_NO_CONTENT)
async def sign_out(
    data: RefreshRequest,
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    await auth_service.sign_out(redis, data.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await auth_service.forgot_password(db, data.email)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    data: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await auth_service.reset_password(db, data.token, data.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/accept-invite", response_model=AuthResponse)
async def accept_invite(
    data: AcceptInviteRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    user_agent, ip = _get_client_info(request)
    return await auth_service.accept_invite(db, redis, data, user_agent, ip)


@router.get("/me", response_model=UserOut)
async def get_me(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await user_service.get_profile(db, current_user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    data: OrgUserUpdate,
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await user_service.update_profile(db, current_user, data)
