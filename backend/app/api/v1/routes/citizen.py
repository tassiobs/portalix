import json
from typing import Annotated, Literal

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_citizen, get_db, get_redis
from app.db.models.citizen import Citizen
from app.schemas.auth import MessageOut
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
    SignedUrlOut,
    UploadOut,
)
from app.schemas.portal import PortalPublicOut, RequestTypeOut
from app.services import citizen_auth as auth_service
from app.services import citizen_requests as request_service
from app.services import storage as storage_service

router = APIRouter(prefix="/customer/{org_slug}/{portal_slug}")

_401 = {401: {"description": "Missing or invalid authentication token"}}
_400 = {400: {"description": "Invalid, expired, or already-used token"}}
_403 = {403: {"description": "Account deactivated, email not verified, or account locked"}}
_404 = {404: {"description": "Portal or resource not found"}}
_409 = {409: {"description": "Email already registered on this portal's org"}}
_423 = {423: {"description": "Account locked due to too many failed login attempts"}}


@router.get(
    "",
    response_model=PortalPublicOut,
    summary="Get portal info 🔓",
    description="Returns the public-facing name, slug, and description of the portal. "
                "Use this to render a branded landing page. No authentication required.",
    tags=["Citizen"],
    responses={**_404},
)
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


@router.post(
    "/auth/sign-up",
    response_model=CitizenSignUpResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Citizen Auth"],
    summary="Customer sign-up 🔓",
    description="Creates a customer account scoped to this org. The customer receives a verification email — "
                "they cannot sign in until the email is confirmed. "
                "If `redirect_url` is provided the verification link is built as `{redirect_url}?token=...`.",
    responses={**_409, **_404},
)
async def sign_up(
    org_slug: str,
    portal_slug: str,
    data: CitizenSignUpRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    return await auth_service.sign_up(db, redis, org_slug, portal_slug, data)


@router.post(
    "/auth/verify-email",
    response_model=MessageOut,
    tags=["Citizen Auth"],
    summary="Verify customer email 🔓",
    description="Consumes the verification token from the email link and marks the account as verified. "
                "Tokens expire after 24 hours and can only be used once.",
    responses={**_400},
)
async def verify_email(
    org_slug: str,
    portal_slug: str,
    data: CitizenVerifyEmailRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await auth_service.verify_email(db, data.token)


@router.post(
    "/auth/sign-in",
    response_model=CitizenAuthResponse,
    tags=["Citizen Auth"],
    summary="Customer sign-in 🔓",
    description="Authenticates a customer and returns a portal-scoped `access_token` and `refresh_token`. "
                "The access token is valid for 30 minutes. The same credentials work on any portal in this org.",
    responses={**_401, **_403, **_404, **_423},
)
async def sign_in(
    org_slug: str,
    portal_slug: str,
    data: CitizenSignInRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    return await auth_service.sign_in(db, redis, org_slug, portal_slug, data.email, data.password)


@router.post(
    "/auth/refresh",
    response_model=CitizenAuthResponse,
    tags=["Citizen Auth"],
    summary="Refresh customer tokens 🔓",
    description="Exchanges a valid refresh token for a new access token and refresh token pair scoped to this portal. "
                "The old refresh token is invalidated on use.",
    responses={401: {"description": "Refresh token invalid, expired, or already used"}},
)
async def refresh(
    org_slug: str,
    portal_slug: str,
    data: CitizenRefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    return await auth_service.refresh_tokens(db, redis, data.refresh_token)


@router.post(
    "/auth/exchange",
    response_model=CitizenAuthResponse,
    tags=["Citizen Auth"],
    summary="Exchange token across portals 🔓",
    description="Exchanges a refresh token from **any portal in the same org** for a new token scoped to this portal. "
                "Use this to silently sign a customer into a second portal without re-authentication. "
                "The customer must belong to the same org as the target portal. "
                "Store the refresh token keyed by `org_slug` (not portal) so it is reusable across portals.",
    responses={
        401: {"description": "Refresh token invalid, expired, or already used"},
        403: {"description": "Token belongs to a different org"},
        **_404,
    },
)
async def exchange_portal_token(
    org_slug: str,
    portal_slug: str,
    data: CitizenExchangeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    return await auth_service.exchange_portal_token(db, redis, org_slug, portal_slug, data.refresh_token)


@router.post(
    "/auth/sign-out",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Citizen Auth"],
    summary="Customer sign-out 🔓",
    description="Invalidates the provided refresh token. The access token remains valid until it expires.",
)
async def sign_out(
    org_slug: str,
    portal_slug: str,
    data: CitizenRefreshRequest,
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    await auth_service.sign_out(redis, data.refresh_token)


@router.post(
    "/auth/forgot-password",
    response_model=MessageOut,
    tags=["Citizen Auth"],
    summary="Request password reset 🔓",
    description="Sends a password reset link to the customer's email. "
                "Always returns the same response regardless of whether the email exists.",
)
async def forgot_password(
    org_slug: str,
    portal_slug: str,
    data: CitizenForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await auth_service.forgot_password(db, org_slug, portal_slug, data.email)


@router.post(
    "/auth/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Citizen Auth"],
    summary="Reset customer password 🔓",
    description="Consumes the reset token and sets a new password. "
                "Also invalidates all existing refresh tokens for the customer. Tokens expire after 1 hour.",
    responses={**_400},
)
async def reset_password(
    org_slug: str,
    portal_slug: str,
    data: CitizenResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await auth_service.reset_password(db, data.token, data.new_password)


@router.get(
    "/auth/me",
    response_model=CitizenOut,
    tags=["Citizen Auth"],
    summary="Get current customer",
    description="Returns the authenticated customer's profile.",
    responses={**_401},
)
async def get_me(
    org_slug: str,
    portal_slug: str,
    citizen: Annotated[Citizen, Depends(get_current_citizen)],
):
    return citizen


@router.get(
    "/request-types",
    response_model=list[RequestTypeOut],
    tags=["Citizen Request Types"],
    summary="List available request types 🔓",
    description="Returns the request types customers can apply for on this portal, including their custom fields. "
                "No authentication required — use this to render the service catalogue before sign-in.",
    responses={**_404},
)
async def list_request_types(
    org_slug: str,
    portal_slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.citizen_auth import _get_portal_by_slug
    portal = await _get_portal_by_slug(db, org_slug, portal_slug)
    return await request_service.list_request_types(db, portal.id)


@router.get(
    "/requests",
    response_model=list[CitizenRequestOut],
    tags=["Citizen Requests"],
    summary="List my requests",
    description="Returns all requests submitted by the authenticated customer on this portal. "
                "Optionally filter by `status`.",
    responses={**_401},
)
async def list_my_requests(
    org_slug: str,
    portal_slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    citizen: Annotated[Citizen, Depends(get_current_citizen)],
    status: Literal["open", "in_progress", "rejected", "closed"] | None = None,
):
    return await request_service.list_citizen_requests(db, citizen.id, citizen.portal_id, status)


@router.post(
    "/requests",
    response_model=CitizenRequestOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Citizen Requests"],
    summary="Submit a request",
    description="Submits a new request of the given type with optional field values. "
                "The `request_type_id` must belong to this portal.",
    responses={**_401, **_404},
)
async def create_request(
    org_slug: str,
    portal_slug: str,
    data: CitizenRequestCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    citizen: Annotated[Citizen, Depends(get_current_citizen)],
):
    return await request_service.create_request(db, citizen, data)


@router.get(
    "/requests/{request_id}",
    response_model=CitizenRequestOut,
    tags=["Citizen Requests"],
    summary="Get a request",
    description="Returns a single request submitted by the authenticated customer. "
                "Returns 404 if the request belongs to a different customer.",
    responses={**_401, **_404},
)
async def get_request(
    org_slug: str,
    portal_slug: str,
    request_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    citizen: Annotated[Citizen, Depends(get_current_citizen)],
):
    return await request_service.get_request(db, citizen, request_id)


@router.post(
    "/uploads",
    response_model=UploadOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Citizen Requests"],
    summary="Upload an attachment",
    description="Uploads a file (PDF, JPEG, PNG — max 10 MB) and returns a `storage_path` "
                "to be passed as the value of a `file` field when submitting a request.",
    responses={**_401, **_404},
)
async def upload_attachment(
    org_slug: str,
    portal_slug: str,
    file: UploadFile,
    citizen: Annotated[Citizen, Depends(get_current_citizen)],
):
    content = await file.read()
    storage_path = await storage_service.upload_file(
        str(citizen.org_id),
        str(citizen.portal_id),
        content,
        file.filename or "upload",
        file.content_type or "application/octet-stream",
    )
    return UploadOut(storage_path=storage_path, file_name=file.filename or "upload")


@router.get(
    "/requests/{request_id}/fields/{field_id}/signed-url",
    response_model=SignedUrlOut,
    tags=["Citizen Requests"],
    summary="Get signed URL for a file field",
    description="Generates a temporary signed URL (valid 1 hour) for a `file` field on the citizen's own request.",
    responses={**_401, **_404},
)
async def get_field_signed_url(
    org_slug: str,
    portal_slug: str,
    request_id: str,
    field_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    citizen: Annotated[Citizen, Depends(get_current_citizen)],
):
    req = await request_service.get_request(db, citizen, request_id)
    fv = next((v for v in req.field_values if str(v.field_id) == field_id), None)
    if not fv or not fv.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found or has no value")
    try:
        data = json.loads(fv.value)
        storage_path: str = data["storage_path"]
        file_name: str = data.get("file_name", "")
    except (json.JSONDecodeError, KeyError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Field value is not a valid file reference")
    signed_url = await storage_service.create_signed_url(storage_path)
    return SignedUrlOut(url=signed_url, file_name=file_name)
