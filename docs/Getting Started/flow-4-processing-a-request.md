---
title: "Flow 4 — Processing a Request"
excerpt: List open requests on a portal and update a request status.
hidden: false
---

**Who runs this**: an internal user (Ana) with access to the portal.

**What it covers**: list open requests → view a request → update its status.

---

### 1. List requests on the portal

```http
GET /org/portals/p9q8r7.../requests
Authorization: Bearer <ana-token>
```

```json
[
  {
    "id": "req123...",
    "portal_id": "p9q8r7...",
    "request_type_id": "rt1rt2...",
    "citizen_id": "c1d2e3...",
    "title": "Solicitação de Licença - Galpão Industrial",
    "status": "open",
    "created_at": "2026-09-21T14:25:00Z"
  }
]
```

---

### 2. Update a request

Ana reviews the submission and moves it to the next status.

```http
PATCH /org/portals/p9q8r7.../requests/req123...
Authorization: Bearer <ana-token>
Content-Type: application/json

{
  "status": "in_progress"
}
```

```json
{
  "id": "req123...",
  "portal_id": "p9q8r7...",
  "request_type_id": "rt1rt2...",
  "citizen_id": "c1d2e3...",
  "title": "Solicitação de Licença - Galpão Industrial",
  "status": "in_progress",
  "created_at": "2026-09-21T14:25:00Z"
}
```

You can also update the `title` in the same call:

```http
PATCH /org/portals/p9q8r7.../requests/req123...
Authorization: Bearer <ana-token>
Content-Type: application/json

{
  "status": "completed",
  "title": "Solicitação de Licença - Galpão Industrial (Aprovada)"
}
```

---

## What's Next

- **Portal Roles** — create custom roles with specific permissions: `POST /org/portals/{portal_id}/roles`
- **Org Settings** — configure lockout policies and MFA requirements: `GET /org/settings`
- **Full API reference** — every endpoint: see the API Reference section
