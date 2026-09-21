---
title: "Flow 1 — Org Setup"
excerpt: Sign up, verify your email, and create your first portal with request types.
hidden: false
---

**Who runs this**: the person who created the org (Org Super Admin).

**What it covers**: sign up → verify email → sign in → create a portal → create request types.

> **Before you start**: All endpoints (except those marked `security: []`) require a Bearer JWT in the `Authorization` header. This flow shows you where to get one.

---

### 1. Sign up

```http
POST /auth/sign-up
Content-Type: application/json

{
  "org_name": "Prefeitura de Maceió",
  "name": "Tassio",
  "email": "tassio@prefeitura.gov.br",
  "password": "supersecret123"
}
```

```json
{
  "user": {
    "id": "a1b2c3...",
    "email": "tassio@prefeitura.gov.br",
    "email_verified": false,
    "status": "active"
  },
  "message": "Account created. Please check your email to verify your account.",
  "verification_token": "<token>"
}
```

A verification email is sent immediately. The account cannot sign in until the email is verified.

> **During development**: the `verification_token` is also returned in the response body so you can verify without email access.

---

### 2. Verify email

```http
POST /auth/verify-email
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
POST /auth/sign-in
Content-Type: application/json

{
  "email": "tassio@prefeitura.gov.br",
  "password": "supersecret123"
}
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "550e8400...",
  "token_type": "bearer",
  "user": {
    "id": "a1b2c3...",
    "email": "tassio@prefeitura.gov.br",
    "email_verified": true,
    "status": "active",
    "org_roles": [{ "name": "Super Admin", "permissions": ["org.users.manage", ...] }]
  }
}
```

Store the `access_token` — every subsequent request needs `Authorization: Bearer <access_token>`.

When the access token expires, use the refresh token:

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "<refresh_token>"
}
```

---

### 4. Create a portal

```http
POST /org/portals
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Licenciamento Ambiental",
  "description": "Portal de solicitações de licença ambiental"
}
```

```json
{
  "id": "p9q8r7...",
  "org_id": "o1o2o3...",
  "name": "Licenciamento Ambiental",
  "slug": "licenciamento-ambiental",
  "description": "Portal de solicitações de licença ambiental",
  "domain": null,
  "created_at": "2026-09-21T14:00:00Z"
}
```

Note the `id` and `slug` — you'll use `id` for admin API calls and `slug` for citizen-facing URLs.

The citizen portal will be accessible at:
```
/{org-slug}/{portal-slug}
```

---

### 5. Create request types

Request types define what citizens can submit on this portal.

```http
POST /org/portals/p9q8r7.../request-types
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Licença de Instalação",
  "description": "Solicitação de licença para instalação de estabelecimento"
}
```

```json
{
  "id": "rt1rt2...",
  "portal_id": "p9q8r7...",
  "name": "Licença de Instalação",
  "description": "Solicitação de licença para instalação de estabelecimento",
  "created_at": "2026-09-21T14:01:00Z"
}
```

Create as many request types as needed. Citizens will choose from this list when submitting a request.

---

**Next**: [Flow 2 — Internal User Onboarding](./flow-2-internal-user-onboarding)
