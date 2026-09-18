import json
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, get_redis
from app.db.models.user import OrgUser
from app.schemas.auth import SessionOut

router = APIRouter(prefix="/auth/sessions", tags=["Sessions"])


async def _get_sessions_for_user(
    redis: aioredis.Redis, user_id: str, current_session_id: str | None = None
) -> list[SessionOut]:
    session_ids = await redis.smembers(f"user_sessions:{user_id}")
    sessions = []

    for sid in session_ids:
        raw = await redis.get(f"session:{sid}")
        if not raw:
            # Stale reference, clean up
            await redis.srem(f"user_sessions:{user_id}", sid)
            continue
        data = json.loads(raw)
        sessions.append(
            SessionOut(
                id=sid,
                user_agent=data.get("user_agent"),
                ip_address=data.get("ip"),
                created_at=data.get("created_at", ""),
                last_used_at=data.get("last_used_at", ""),
                expires_at=data.get("expires_at", ""),
                is_current=(sid == current_session_id),
            )
        )

    return sessions


def _extract_session_id_from_request(request: Request) -> str | None:
    """Best-effort: look for session_id in a custom header or query param."""
    return request.headers.get("x-session-id") or request.query_params.get("session_id")


@router.get("", response_model=list[SessionOut])
async def list_sessions(
    request: Request,
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    current_session_id = _extract_session_id_from_request(request)
    return await _get_sessions_for_user(redis, str(current_user.id), current_session_id)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_all_sessions(
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    """Revoke all active sessions for the current user."""
    session_ids = await redis.smembers(f"user_sessions:{current_user.id}")
    for sid in session_ids:
        await redis.delete(f"session:{sid}")
    await redis.delete(f"user_sessions:{current_user.id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: str,
    current_user: Annotated[OrgUser, Depends(get_current_active_user)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    """Revoke a specific session."""
    raw = await redis.get(f"session:{session_id}")
    if raw:
        data = json.loads(raw)
        # Ensure the session belongs to the current user
        if data.get("user_id") == str(current_user.id):
            await redis.delete(f"session:{session_id}")
            await redis.srem(f"user_sessions:{current_user.id}", session_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
