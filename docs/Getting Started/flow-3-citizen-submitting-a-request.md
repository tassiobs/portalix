---
title: "Flow 3 — Citizen Submitting a Request"
excerpt: Sign up on a portal, verify email, sign in, and submit a request.
hidden: false
---

**Who runs this**: a citizen accessing the portal.

**What it covers**: sign up → verify email → sign in → list request types → submit a request.

> **Note**: all citizen endpoints are scoped to a specific org and portal via the URL path. A citizen account on one portal cannot be used on another.

---

### 1. Sign up on the portal

The citizen registers using the org slug and portal slug from Flow 1.

```http
POST /citizen/{org_slug}/{portal_slug}/auth/sign-up
Content-Type: application/json

{
  "name": "João Silva",
  "email": "joao@empresa.com.br",
  "password": "minhasenha456"
}
```

```json
{
  "citizen": {
    "id": "c1d2e3...",
    "portal_id": "p9q8r7...",
    "name": "João Silva",
    "email": "joao@empresa.com.br",
    "email_verified": false,
    "status": "active",
    "created_at": "2026-09-21T14:20:00Z"
  },
  "message": "Account created. Please check your email to verify your account.",
  "verification_token": "<token>"
}
```

> **During development**: the `verification_token` is also returned in the response body so you can verify without email access.

---

### 2. Verify email

```http
POST /citizen/{org_slug}/{portal_slug}/auth/verify-email
Content-Type: application/json

{
  "token": "<verification_token from step 1>"
}
```

```json
{
  "message": "Email verified. You can now sign in."
}
```

---

### 3. Sign in

```http
POST /citizen/{org_slug}/{portal_slug}/auth/sign-in
Content-Type: application/json

{
  "email": "joao@empresa.com.br",
  "password": "minhasenha456"
}
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "550e8400...",
  "token_type": "bearer",
  "citizen": {
    "id": "c1d2e3...",
    "portal_id": "p9q8r7...",
    "name": "João Silva",
    "email": "joao@empresa.com.br",
    "email_verified": true,
    "status": "active",
    "created_at": "2026-09-21T14:20:00Z"
  }
}
```

Store the `access_token` — every subsequent citizen request needs `Authorization: Bearer <access_token>`.

---

### 4. Browse available request types

```http
GET /citizen/{org_slug}/{portal_slug}/request-types
Authorization: Bearer <access_token>
```

```json
[
  {
    "id": "rt1rt2...",
    "portal_id": "p9q8r7...",
    "name": "Licença de Instalação",
    "description": "Solicitação de licença para instalação de estabelecimento",
    "created_at": "2026-09-21T14:01:00Z"
  }
]
```

---

### 5. Submit a request

```http
POST /citizen/{org_slug}/{portal_slug}/requests
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "request_type_id": "rt1rt2...",
  "title": "Solicitação de Licença - Galpão Industrial"
}
```

```json
{
  "id": "req123...",
  "portal_id": "p9q8r7...",
  "request_type_id": "rt1rt2...",
  "citizen_id": "c1d2e3...",
  "title": "Solicitação de Licença - Galpão Industrial",
  "status": "open",
  "created_at": "2026-09-21T14:25:00Z"
}
```

João can check on his request at any time:

```http
GET /citizen/{org_slug}/{portal_slug}/requests
Authorization: Bearer <access_token>
```

Or fetch a specific one:

```http
GET /citizen/{org_slug}/{portal_slug}/requests/req123...
Authorization: Bearer <access_token>
```

---

**Next**: [Flow 4 — Processing a Request](./flow-4-processing-a-request)
