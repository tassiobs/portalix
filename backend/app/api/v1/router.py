from fastapi import APIRouter

from app.api.v1.routes import (
    auth,
    org,
    org_invitations,
    org_permissions,
    org_roles,
    org_settings,
    org_users,
    requests,
    sessions,
)

router = APIRouter()

router.include_router(auth.router)
router.include_router(org.router)
router.include_router(org_settings.router)
router.include_router(org_users.router)
router.include_router(org_roles.router)
router.include_router(org_permissions.router)
router.include_router(org_invitations.router)
router.include_router(sessions.router)
router.include_router(requests.router)
