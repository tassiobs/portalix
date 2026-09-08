---
title: "Flow 2 — Internal User Onboarding"
excerpt: Add an org user, grant them portal access, and assign a role with an ABAC scope.
hidden: false
---

**Who runs this**: an org admin with `org.users.manage` and `portal.users.manage` permissions.

**What it covers**: add an org user → add them to a portal → assign a role with an ABAC scope.

---

### 1. Add an org user

```http
POST /api/v1/org/users
Authorization: Bearer <token>
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
  "status": "active",
  "emailVerified": false
}
```

An invitation email is sent to Ana. She sets her password via the link.

### 2. Add her to a portal

```http
POST /api/v1/portals/p9q8r7.../users
Authorization: Bearer <token>
Content-Type: application/json

{
  "userId": "u5v6w7..."
}
```

```json
{
  "id": "u5v6w7...",
  "email": "ana@prefeitura.gov.br",
  "status": "active",
  "roleAssignments": [],
  "addedAt": "2026-09-08T14:10:00Z"
}
```

### 3. Assign a portal role with an ABAC scope

First, get the available roles to find the right `roleId`:

```http
GET /api/v1/portals/p9q8r7.../roles
Authorization: Bearer <token>
```

Then assign the role, scoped to Ana's department only:

```http
POST /api/v1/portals/p9q8r7.../users/u5v6w7.../roles
Authorization: Bearer <token>
Content-Type: application/json

{
  "roleId": "role-analyst-id...",
  "scope": {
    "departmentIds": ["d1e2f3..."],
    "onlyAssignedToSelf": false
  }
}
```

Ana can now access the portal, but only sees request types, requests, and tasks belonging to the `Análise Técnica` department.

---

**Next**: [Flow 3 — Citizen Submitting a Request](./flow-3-citizen-submitting-a-request)
