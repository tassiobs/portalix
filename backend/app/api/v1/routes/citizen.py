from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_citizen, get_db, get_redis
from app.db.models.citizen import Citizen
from app.schemas.citizen import (
    CitizenAuthResponse,
    CitizenForgotPasswordRequest,
    CitizenOut,
    CitizenRefreshRequest,
    CitizenRequestCreate,
    CitizenRequestOut,
    CitizenResetPasswordRequest,
    CitizenSignInRequest,
    CitizenSignUpRequest,
    CitizenSignUpResponse,
    CitizenVerifyEmailRequest,
)
from app.schemas.portal import RequestTypeOut
from app.services import citizen_auth as auth_service
from app.services import citizen_requests as request_service

router = APIRouter(prefix="/citizen/{org_slug}/{portal_slug}", tags=["citizen"])


@router.post("/auth/sign-up", response_model=CitizenSignUpResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(
    org_slug: str,
    portal_slug: str,
    data: CitizenSignUpRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    return await auth_service.sign_up(db, redis, org_slug, portal_slug, data)


@router.post("/auth/verify-email")
async def verify_email(
    data: CitizenVerifyEmailRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await auth_service.verify_email(db, data.token)


@router.post("/auth/sign-in", response_model=CitizenAuthResponse)
async def sign_in(
    org_slug: str,
    portal_slug: str,
    data: CitizenSignInRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    return await auth_service.sign_in(db, redis, org_slug, portal_slug, data.email, data.password)


@router.post("/auth/refresh", response_model=CitizenAuthResponse)
async def refresh(
    data: CitizenRefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    return await auth_service.refresh_tokens(db, redis, data.refresh_token)


@router.post("/auth/sign-out", status_code=status.HTTP_204_NO_CONTENT)
async def sign_out(
    data: CitizenRefreshRequest,
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    await auth_service.sign_out(redis, data.refresh_token)


@router.post("/auth/forgot-password")
async def forgot_password(
    org_slug: str,
    portal_slug: str,
    data: CitizenForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await auth_service.forgot_password(db, org_slug, portal_slug, data.email)


@router.post("/auth/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    data: CitizenResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await auth_service.reset_password(db, data.token, data.new_password)


@router.get("/auth/me", response_model=CitizenOut)
async def get_me(
    citizen: Annotated[Citizen, Depends(get_current_citizen)],
):
    return citizen


@router.get("/request-types", response_model=list[RequestTypeOut])
async def list_request_types(
    org_slug: str,
    portal_slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.citizen_auth import _get_portal_by_slug
    portal = await _get_portal_by_slug(db, org_slug, portal_slug)
    return await request_service.list_request_types(db, portal.id)


@router.get("/requests", response_model=list[CitizenRequestOut])
async def list_my_requests(
    db: Annotated[AsyncSession, Depends(get_db)],
    citizen: Annotated[Citizen, Depends(get_current_citizen)],
):
    return await request_service.list_citizen_requests(db, citizen.id, citizen.portal_id)


@router.post("/requests", response_model=CitizenRequestOut, status_code=status.HTTP_201_CREATED)
async def create_request(
    data: CitizenRequestCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    citizen: Annotated[Citizen, Depends(get_current_citizen)],
):
    return await request_service.create_request(db, citizen, data)


@router.get("/requests/{request_id}", response_model=CitizenRequestOut)
async def get_request(
    request_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    citizen: Annotated[Citizen, Depends(get_current_citizen)],
):
    return await request_service.get_request(db, citizen, request_id)
