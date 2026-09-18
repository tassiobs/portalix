from typing import Annotated
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.base import AsyncSessionLocal
from app.db.models.rbac import OrgRolePermission, OrgUserRole
from app.db.models.user import OrgUser

bearer_scheme = HTTPBearer()

_redis_client: aioredis.Redis | None = None


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
) -> OrgUser:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await db.execute(
        select(OrgUser)
        .where(OrgUser.id == UUID(user_id))
        .options(
            selectinload(OrgUser.user_roles).selectinload(OrgUserRole.role)
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Check tokens_invalidated_at against token iat
    iat = payload.get("iat")
    if user.tokens_invalidated_at and iat:
        from datetime import datetime
        invalidated_ts = user.tokens_invalidated_at.timestamp()
        if iat < invalidated_ts:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been invalidated")

    return user


async def get_current_active_user(
    user: Annotated[OrgUser, Depends(get_current_user)],
) -> OrgUser:
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is not active")
    return user


def require_permissions(*perms: str):
    """Returns a dependency that checks the current user has at least one of the given permissions."""

    async def _dependency(
        user: Annotated[OrgUser, Depends(get_current_active_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> OrgUser:
        if user.is_super_admin:
            return user

        result = await db.execute(
            select(OrgRolePermission).join(OrgUserRole, OrgUserRole.role_id == OrgRolePermission.role_id).where(
                OrgUserRole.user_id == user.id,
                OrgRolePermission.permission.in_(perms),
            )
        )
        found = result.scalars().first()
        if not found:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return _dependency
