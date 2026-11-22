from typing import Annotated, Literal

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_citizen, get_db, get_redis
from app.db.models.citizen import Citizen
from app.schemas.citizen import (
    CitizenAuthResponse,
    CitizenExchangeRequest,
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
from app.schemas.portal import PortalPublicOut, RequestTypeOut
from app.services import citizen_auth as auth_service
from app.services import citizen_requests as request_service

router = APIRouter(prefix="/customer/{org_slug}/{portal_slug}")


@router.get("", response_model=PortalPublicOut, summary="Get public portal info", tags=["Citizen"])
async def get_portal_info(
    org_slug: str,
    portal_slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.citizen_auth import _get_org_by_slug, _get_portal_by_slug
    org = await _get_org_by_slug(db, org_slug)
    portal = await _get_portal_by_slug(db, org_slug, portal_slug)
    return PortalPublicOut(
        name=portal.name,
        slug=portal.slug,
        description=portal.description,
        org_slug=org.slug,
    )


@router.post("/auth/sign-up", response_model=CitizenSignUpResponse, status_code=status.HTTP_201_CREATED, tags=["Citizen Auth"])
async def sign_up(
    org_slug: str,
    portal_slug: str,
    data: CitizenSignUpRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    return await auth_service.sign_up(db, redis, org_slug, portal_slug, data)


@router.post("/auth/verify-email", tags=["Citizen Auth"])
async def verify_email(
    org_slug: str,
    portal_slug: str,
    data: CitizenVerifyEmailRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await auth_service.verify_email(db, data.token)


@router.post("/auth/sign-in", response_model=CitizenAuthResponse, tags=["Citizen Auth"])
async def sign_in(
    org_slug: str,
    portal_slug: str,
    data: CitizenSignInRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    return await auth_service.sign_in(db, redis, org_slug, portal_slug, data.email, data.password)


@router.post("/auth/refresh", response_model=CitizenAuthResponse, tags=["Citizen Auth"])
async def refresh(
    org_slug: str,
    portal_slug: str,
    data: CitizenRefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    return await auth_service.refresh_tokens(db, redis, data.refresh_token)


@router.post("/auth/exchange", response_model=CitizenAuthResponse, tags=["Citizen Auth"])
async def exchange_portal_token(
    org_slug: str,
    portal_slug: str,
    data: CitizenExchangeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    return await auth_service.exchange_portal_token(db, redis, org_slug, portal_slug, data.refresh_token)


@router.post("/auth/sign-out", status_code=status.HTTP_204_NO_CONTENT, tags=["Citizen Auth"])
async def sign_out(
    org_slug: str,
    portal_slug: str,
    data: CitizenRefreshRequest,
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    await auth_service.sign_out(redis, data.refresh_token)


@router.post("/auth/forgot-password", tags=["Citizen Auth"])
async def forgot_password(
    org_slug: str,
    portal_slug: str,
    data: CitizenForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await auth_service.forgot_password(db, org_slug, portal_slug, data.email)


@router.post("/auth/reset-password", status_code=status.HTTP_204_NO_CONTENT, tags=["Citizen Auth"])
async def reset_password(
    org_slug: str,
    portal_slug: str,
    data: CitizenResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await auth_service.reset_password(db, data.token, data.new_password)


@router.get("/auth/me", response_model=CitizenOut, tags=["Citizen Auth"])
async def get_me(
    org_slug: str,
    portal_slug: str,
    citizen: Annotated[Citizen, Depends(get_current_citizen)],
):
    return citizen


@router.get("/request-types", response_model=list[RequestTypeOut], tags=["Citizen Request Types"])
async def list_request_types(
    org_slug: str,
    portal_slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.citizen_auth import _get_portal_by_slug
    portal = await _get_portal_by_slug(db, org_slug, portal_slug)
    return await request_service.list_request_types(db, portal.id)


@router.get("/requests", response_model=list[CitizenRequestOut], tags=["Citizen Requests"])
async def list_my_requests(
    org_slug: str,
    portal_slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    citizen: Annotated[Citizen, Depends(get_current_citizen)],
    status: Literal["open", "in_progress", "rejected", "closed"] | None = None,
):
    return await request_service.list_citizen_requests(db, citizen.id, citizen.portal_id, status)


@router.post("/requests", response_model=CitizenRequestOut, status_code=status.HTTP_201_CREATED, tags=["Citizen Requests"])
async def create_request(
    org_slug: str,
    portal_slug: str,
    data: CitizenRequestCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    citizen: Annotated[Citizen, Depends(get_current_citizen)],
):
    return await request_service.create_request(db, citizen, data)


@router.get("/requests/{request_id}", response_model=CitizenRequestOut, tags=["Citizen Requests"])
async def get_request(
    org_slug: str,
    portal_slug: str,
    request_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    citizen: Annotated[Citizen, Depends(get_current_citizen)],
):
    return await request_service.get_request(db, citizen, request_id)
