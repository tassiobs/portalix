from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, get_redis
from app.db.models.user import OrgUser
from app.schemas.auth import (
    AcceptInviteRequest,
    AuthResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    MessageOut,
    RefreshRequest,
    ResendVerificationRequest,
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

_401 = {401: {"description": "Missing or invalid authentication token"}}
_400 = {400: {"description": "Invalid, expired, or already-used token"}}
_403 = {403: {"description": "Account deactivated or email not verified"}}
_409 = {409: {"description": "Email address already registered"}}
_423 = {423: {"description": "Account locked due to too many failed login attempts"}}


def _get_client_info(request: Request) -> tuple[str | None, str | None]:
    user_agent = request.headers.get("user-agent")
    ip = request.client.host if request.client else None
    return user_agent, ip


@router.post(
    "/sign-up",
    response_model=SignUpResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create org and admin account 🔓",
    description="Creates a new organization and the founding Super Admin user in a single call. "
                "The user receives a verification email — they cannot sign in until the email is confirmed.",
    responses={**_409},
)
async def sign_up(
    data: SignUpRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    return await auth_service.sign_up(db, redis, data)


@router.post(
    "/verify-email",
    response_model=MessageOut,
    summary="Verify email address 🔓",
    description="Consumes the token from the verification email link and marks the user's email as verified. "
                "Tokens expire after 24 hours and can only be used once.",
    responses={**_400},
)
async def verify_email(
    data: VerifyEmailRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await auth_service.verify_email(db, data.token)


@router.post(
    "/resend-verification",
    response_model=MessageOut,
    summary="Resend verification email 🔓",
    description="Sends a new verification email to the given address. "
                "Silently succeeds if the email is not found to prevent enumeration.",
)
async def resend_verification(
    body: ResendVerificationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await auth_service.resend_verification(db, body.email, body.redirect_url)


@router.post(
    "/sign-in",
    response_model=AuthResponse,
    summary="Sign in 🔓",
    description="Authenticates a staff user and returns a short-lived `access_token` (JWT) "
                "and a long-lived `refresh_token`. Use the access token as `Authorization: Bearer <token>` "
                "on subsequent requests.",
    responses={**_401, **_403, **_423},
)
async def sign_in(
    data: SignInRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    user_agent, ip = _get_client_info(request)
    return await auth_service.sign_in(db, redis, data.email, data.password, user_agent, ip)


@router.post(
    "/refresh",
    response_model=AuthResponse,
    summary="Refresh tokens 🔓",
    description="Exchanges a valid refresh token for a new access token and refresh token pair. "
                "The old refresh token is invalidated on use.",
    responses={401: {"description": "Refresh token invalid, expired, or already used"}},
)
async def refresh(
    data: RefreshRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    user_agent, ip = _get_client_info(request)
    return await auth_service.refresh_tokens(db, redis, data.refresh_token, user_agent, ip)


@router.post(
    "/sign-out",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Sign out 🔓",
    description="Invalidates the provided refresh token. The access token continues to work until it expires "
                "(up to 30 minutes) — clients should discard it immediately.",
)
async def sign_out(
    data: RefreshRequest,
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    await auth_service.sign_out(redis, data.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="Request password reset 🔓",
    description="Sends a password reset link to the given email address. "
                "Always returns the same response regardless of whether the email exists, to prevent enumeration.",
)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await auth_service.forgot_password(db, data.email)


@router.post(
    "/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reset password 🔓",
    description="Consumes the token from the reset email and sets a new password. "
                "Also invalidates all existing refresh tokens for the user. Tokens expire after 1 hour.",
    responses={**_400},
)
async def reset_password(
    data: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await auth_service.reset_password(db, data.token, data.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/accept-invite",
    response_model=AuthResponse,
    summary="Accept invitation and set password 🔓",
    description="Consumes an invitation token, sets the user's password, and returns auth tokens. "
                "The user is immediately signed in after accepting. Tokens expire after 7 days.",
    responses={**_400, 409: {"description": "Invitation already accepted"}},
)
async def accept_invite(
    data: AcceptInviteRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    user_agent, ip = _get_client_info(request)
    return await auth_service.accept_invite(db, redis, data, user_agent, ip)


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current user profile",
    description="Returns the authenticated user's profile including their org and portal role assignments.",
    responses={**_401},
)
async def get_me(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await user_service.get_profile(db, current_user)


@router.patch(
    "/me",
    response_model=UserOut,
    summary="Update current user profile",
    description="Updates the authenticated user's name. Email changes are not supported via this endpoint.",
    responses={**_401},
)
async def update_me(
    data: OrgUserUpdate,
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await user_service.update_profile(db, current_user, data)
