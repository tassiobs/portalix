from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.api.v1.router import router
from app.db.base import Base, engine

DESCRIPTION = """
Portalu lets organisations create customer-facing service portals.
Staff sign up, build portals, define request types, and process incoming requests.
Customers sign up to a portal, submit requests, and track their progress.

## Authentication

Two independent token families:

| Scheme | Who | How to obtain |
|---|---|---|
| **StaffBearer** | Org staff / admins | `POST /api/v1/auth/sign-in` |
| **CustomerBearer** | Portal customers | `POST /api/v1/customer/{org_slug}/{portal_slug}/auth/sign-in` |

Endpoints marked 🔓 require no token.

## Permissions

Staff endpoints require specific permission keys on the caller's role.
The required permission is noted in each operation description.
Fetch the full list from `GET /api/v1/org/permissions` (org-level) or `GET /api/v1/org/portals/permissions` (portal-level).
"""

TAGS_METADATA = [
    {"name": "Auth", "description": "Staff sign-up, sign-in, token refresh, password reset. 🔓 Public endpoints require no token."},
    {"name": "Sessions", "description": "List and revoke active staff sessions."},
    {"name": "Org", "description": "Retrieve and update the authenticated user's organization."},
    {"name": "Org Settings", "description": "Org-wide security settings (lockout, MFA, identity scope)."},
    {"name": "Org Users", "description": "Invite and manage staff members."},
    {"name": "Org Invitations", "description": "Manage pending email invitations."},
    {"name": "Org Roles", "description": "Create and manage permission roles."},
    {"name": "Org Permissions", "description": "List available org-level permission keys."},
    {"name": "Portals", "description": "Create and manage customer-facing portals. Requires `org.users.manage` for write operations."},
    {"name": "Portal Users", "description": "Assign org users to a portal with a portal-scoped role. Requires `portal.users:manage`."},
    {"name": "Request Types", "description": "Define the services customers can apply for. Requires `portal.request_types:manage`."},
    {"name": "Request Type Fields", "description": "Add custom fields to request types."},
    {"name": "Portal Requests", "description": "Admin view of customer requests on a portal."},
    {"name": "Workflows", "description": "Define and retrieve task workflows for request types."},
    {"name": "Tasks", "description": "View and action workflow task instances on a request."},
    {"name": "Task Comments", "description": "Add and list comments on a task instance."},
    {"name": "Requests", "description": "Org-level request management (independent of portals)."},
    {"name": "Citizen Auth", "description": "Customer sign-up, sign-in, token exchange, and password reset. 🔓 Most endpoints are public."},
    {"name": "Citizen Request Types", "description": "Public list of request types available on a portal. 🔓 No token required."},
    {"name": "Citizen Requests", "description": "Customer-submitted requests. Requires CustomerBearer token."},
    {"name": "Citizen", "description": "Public portal info. 🔓 No token required."},
]

# Customer paths that require no token
_CUSTOMER_PUBLIC_SUFFIXES = {
    "/auth/sign-up",
    "/auth/verify-email",
    "/auth/sign-in",
    "/auth/refresh",
    "/auth/exchange",
    "/auth/sign-out",
    "/auth/forgot-password",
    "/auth/reset-password",
}

# Staff paths that require no token
_STAFF_PUBLIC_PATHS = {
    ("post", "/api/v1/auth/sign-up"),
    ("post", "/api/v1/auth/verify-email"),
    ("post", "/api/v1/auth/resend-verification"),
    ("post", "/api/v1/auth/sign-in"),
    ("post", "/api/v1/auth/refresh"),
    ("post", "/api/v1/auth/forgot-password"),
    ("post", "/api/v1/auth/reset-password"),
    ("post", "/api/v1/auth/accept-invite"),
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Portalu API",
    version="2.4.0",
    lifespan=lifespan,
    servers=[{"url": "https://portalu-production.up.railway.app", "description": "Production"}],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=DESCRIPTION,
        routes=app.routes,
        servers=app.servers,
        tags=TAGS_METADATA,
    )

    schema.setdefault("components", {})["securitySchemes"] = {
        "StaffBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT for org staff users. Obtain via `POST /api/v1/auth/sign-in`.",
        },
        "CustomerBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT for portal customers. Obtain via `POST /api/v1/customer/{org_slug}/{portal_slug}/auth/sign-in`.",
        },
    }

    customer_prefix = "/api/v1/customer/"

    for path, path_item in schema.get("paths", {}).items():
        for method, operation in path_item.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue

            if path.startswith(customer_prefix):
                is_public = (
                    any(path.endswith(s) for s in _CUSTOMER_PUBLIC_SUFFIXES)
                    or (method == "get" and path == "/api/v1/customer/{org_slug}/{portal_slug}")
                    or (method == "get" and path.endswith("/request-types"))
                )
                operation["security"] = [] if is_public else [{"CustomerBearer": []}]
            elif (method, path) in _STAFF_PUBLIC_PATHS:
                operation["security"] = []
            else:
                operation["security"] = [{"StaffBearer": []}]

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
