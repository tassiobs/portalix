---
title: "Flow 2 — Internal User Onboarding"
excerpt: Invite an org user, assign an org role, then grant portal access with a portal role.
hidden: false
---

**Who runs this**: the Org Super Admin (or any user with `org.users.manage`).

**What it covers**: invite a user → assign an org role → add them to a portal with a portal role.

---

### 1. Invite a user to the org

```http
POST /org/users
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Ana Lima",
  "email": "ana@prefeitura.gov.br"
}
```

```json
{
  "id": "u5v6w7...",
  "name": "Ana Lima",
  "email": "ana@prefeitura.gov.br",
  "email_verified": false,
  "status": "active",
  "org_roles": [],
  "created_at": "2026-09-21T14:10:00Z",
  "invitation_token": "<token>"
}
```

An invitation email is sent to Ana with a link to set her password. The `invitation_token` is also returned in the response body for development convenience.

> **During development**: use `POST /auth/accept-invite` with `{ "token": "<invitation_token>", "password": "..." }` to accept the invite without email access.

---

### 2. Assign an org-level role

Org roles control what Ana can do at the organisation level (manage users, settings, etc.).

First, list available org roles:

```http
GET /org/roles
Authorization: Bearer <access_token>
```

Then assign the role:

```http
POST /org/users/u5v6w7.../roles
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "role_id": "<role-id>"
}
```

Returns `204 No Content` on success.

---

### 3. Add her to a portal

Portal access is separate from org access. Get the portal roles first:

```http
GET /org/portals/p9q8r7.../roles
Authorization: Bearer <access_token>
```

```json
[
  {
    "id": "role-abc...",
    "portal_id": "p9q8r7...",
    "name": "Portal Super Admin",
    "description": null,
    "permissions": ["portal.requests:read", "portal.requests:update", "portal.request_types:manage", "portal.users:manage", "portal.settings:manage"],
    "is_default": true,
    "created_at": "2026-09-21T14:01:00Z"
  }
]
```

Then assign Ana to the portal with a role:

```http
POST /org/portals/p9q8r7.../users
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": "u5v6w7...",
  "role_id": "role-abc..."
}
```

Returns `204 No Content`. Ana can now access this portal and act according to her assigned portal role's permissions.

---

**Next**: [Flow 3 — Citizen Submitting a Request](./flow-3-citizen-submitting-a-request)
