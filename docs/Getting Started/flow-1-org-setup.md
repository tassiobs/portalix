---
title: "Flow 1 — Org Setup"
excerpt: Sign up, verify your email, create a portal, a department, and your first request type.
hidden: false
---

**Who runs this**: the person who created the org (Org Super Admin).

**What it covers**: sign up → verify email → create a portal → create a department → create a request type with fields.

> **Before you start**: All endpoints (except those marked `security: []`) require a Bearer JWT in the `Authorization` header. This flow shows you where to get one.

---

### 1. Sign up

```http
POST /api/v1/auth/sign-up
Content-Type: application/json

{
  "email": "tassio@prefeitura.gov.br",
  "password": "supersecret123",
  "name": "Tassio"
}
```

```json
{
  "user": { "id": "a1b2c3...", "email": "tassio@prefeitura.gov.br", "emailVerified": false },
  "message": "Verification email sent. Please check your inbox."
}
```

A verification email is sent immediately. The account cannot sign in until the email is verified.

### 2. Verify email

```http
POST /api/v1/auth/verify-email
Content-Type: application/json

{
  "token": "<token from email>"
}
```

```json
{
  "token": "eyJhbGciOiJIUzI1NiJ9...",
  "user": { "id": "a1b2c3...", "email": "tassio@prefeitura.gov.br", "emailVerified": true }
}
```

Store the `token` — every subsequent request needs `Authorization: Bearer <token>`.

### 3. Create a portal

```http
POST /api/v1/portals
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Licenciamento Ambiental",
  "description": "Portal de solicitações de licença ambiental"
}
```

```json
{
  "id": "p9q8r7...",
  "name": "Licenciamento Ambiental",
  "status": "active",
  "clientDomain": "licenciamento.portalu.io",
  "adminDomain": "admin.licenciamento.portalu.io",
  "createdAt": "2026-09-08T14:00:00Z"
}
```

Note the `id` — you'll use it as `{portalId}` in every subsequent portal-scoped call.

### 4. Create a department

```http
POST /api/v1/portals/p9q8r7.../departments
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Análise Técnica"
}
```

```json
{
  "id": "d1e2f3...",
  "name": "Análise Técnica",
  "createdAt": "2026-09-08T14:01:00Z"
}
```

### 5. Create a request type

```http
POST /api/v1/portals/p9q8r7.../request-types
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Licença de Instalação",
  "departmentId": "d1e2f3...",
  "status": "active",
  "sla": { "durationHours": 72 },
  "fields": [
    { "name": "Razão Social", "type": "text", "required": true, "order": 1 },
    { "name": "CNPJ", "type": "text", "required": true, "order": 2 },
    { "name": "Planta Baixa", "type": "file_upload", "required": true, "order": 3 },
    { "name": "Tipo de Atividade", "type": "single_dropdown", "required": true, "order": 4,
      "options": [
        { "label": "Industrial", "value": "industrial" },
        { "label": "Comercial", "value": "comercial" }
      ]
    }
  ]
}
```

```json
{
  "id": "rt1rt2...",
  "name": "Licença de Instalação",
  "status": "active",
  "department": { "id": "d1e2f3...", "name": "Análise Técnica" },
  "sla": { "durationHours": 72 },
  "fields": [...]
}
```

The portal is now ready to receive citizen requests.

---

**Next**: [Flow 2 — Internal User Onboarding](./flow-2-internal-user-onboarding)
