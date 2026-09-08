---
title: Core Flows
excerpt: End-to-end walkthroughs of the four main API flows — from org setup to processing a citizen request.
hidden: false
---

This guide walks through the four flows you need to understand to work with the portalu API. Each section shows the exact calls to make, in order, with real request and response examples.

> **Before you start**: All endpoints (except those marked `security: []`) require a Bearer JWT in the `Authorization` header. Each flow below shows you where to get one.

---

## Flow 1 — Org Setup

**Who runs this**: the person who created the org (Org Super Admin).

**What it covers**: sign up → verify email → create a portal → create a department → create a request type with fields.

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

## Flow 2 — Internal User Onboarding

**Who runs this**: an org admin with `org.users.manage` and `portal.users.manage` permissions.

**What it covers**: add an org user → add them to a portal → assign a role with an ABAC scope.

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

## Flow 3 — Citizen Submitting a Request

**Who runs this**: a citizen accessing the portal's client-facing domain.

**What it covers**: sign up → browse request types → stage a file → submit a request.

> **Note**: citizen auth endpoints are scoped to a specific portal. Use `/portals/{portalId}/client/...` — a citizen JWT from one portal cannot be used on another.

### 1. Sign up on the portal

```http
POST /api/v1/portals/p9q8r7.../client/auth/sign-up
Content-Type: application/json

{
  "email": "joao@empresa.com.br",
  "password": "minhasenha456",
  "name": "João Silva"
}
```

```json
{
  "token": "eyJhbGciOiJIUzI1NiJ9...",
  "citizen": { "id": "c1d2e3...", "email": "joao@empresa.com.br", "name": "João Silva" }
}
```

Store the citizen `token` for all subsequent client-context calls.

### 2. Browse available request types

```http
GET /api/v1/portals/p9q8r7.../client/request-types
Authorization: Bearer <citizen-token>
```

```json
[
  {
    "id": "rt1rt2...",
    "name": "Licença de Instalação",
    "status": "active",
    "sla": { "durationHours": 72 }
  }
]
```

### 3. Stage a file

`file_upload` fields require a two-step process: upload first, then reference the ID at submission.

```http
POST /api/v1/uploads/stage
Authorization: Bearer <citizen-token>
Content-Type: multipart/form-data

name=Planta Baixa Galpão
file=<binary PDF>
```

```json
{
  "stagedFileId": "sf9sf8...",
  "name": "Planta Baixa Galpão",
  "mimeType": "application/pdf",
  "sizeBytes": 204800,
  "expiresAt": "2026-09-08T15:30:00Z"
}
```

The `stagedFileId` expires in 1 hour — include it in the request submission before then.

### 4. Submit the request

```http
POST /api/v1/portals/p9q8r7.../client/requests
Authorization: Bearer <citizen-token>
Content-Type: application/json

{
  "requestTypeId": "rt1rt2...",
  "name": "Solicitação de Licença - Galpão Industrial",
  "fieldValues": [
    { "fieldId": "<Razão Social field id>", "value": "Empresa XYZ Ltda" },
    { "fieldId": "<CNPJ field id>", "value": "12.345.678/0001-99" },
    { "fieldId": "<Planta Baixa field id>", "value": "sf9sf8..." },
    { "fieldId": "<Tipo de Atividade field id>", "value": "industrial" }
  ]
}
```

```json
{
  "id": "req123...",
  "protocolNumber": "LIC-2026-000001",
  "status": "open",
  "name": "Solicitação de Licença - Galpão Industrial",
  "requester": { "id": "c1d2e3...", "name": "João Silva" },
  "createdAt": "2026-09-08T14:30:00Z"
}
```

The citizen can track their request using the `protocolNumber`.

---

## Flow 4 — Processing a Request

**Who runs this**: an internal user (Ana) with `portal.requests.manage` permission.

**What it covers**: list open requests → complete a task requesting clarification → citizen responds → approve and complete.

### 1. List open requests

```http
GET /api/v1/portals/p9q8r7.../requests?status=open
Authorization: Bearer <ana-token>
```

```json
{
  "data": [
    {
      "id": "req123...",
      "protocolNumber": "LIC-2026-000001",
      "status": "open",
      "name": "Solicitação de Licença - Galpão Industrial",
      "requester": { "name": "João Silva" }
    }
  ],
  "pagination": { "page": 1, "perPage": 20, "total": 1, "totalPages": 1 }
}
```

Ana's results are silently filtered by her ABAC scope — she only sees requests belonging to `Análise Técnica`.

### 2. Complete a task requesting clarification

The request has an active task. Ana reviews the documents and needs more information.

```http
POST /api/v1/portals/p9q8r7.../requests/req123.../tasks/task456.../complete
Authorization: Bearer <ana-token>
Content-Type: application/json

{
  "outcome": "clarification_requested",
  "notes": "A planta baixa não indica a área de armazenamento de resíduos. Por favor, reenviar com essa informação."
}
```

```json
{
  "id": "task456...",
  "status": "completed",
  "outcome": "clarification_requested"
}
```

The request status moves to `pending_clarification`. A follow-up message is automatically created on the thread with Ana's notes, visible to the citizen.

### 3. Citizen responds with clarification

João receives a notification and replies via the client portal.

```http
POST /api/v1/portals/p9q8r7.../client/requests/req123.../follow-ups
Authorization: Bearer <citizen-token>
Content-Type: application/json

{
  "type": "clarification_response",
  "message": "Segue planta baixa atualizada com a área de armazenamento indicada."
}
```

```json
{
  "id": "fu789...",
  "type": "clarification_response",
  "message": "Segue planta baixa atualizada com a área de armazenamento indicada.",
  "createdAt": "2026-09-08T16:00:00Z"
}
```

To attach the updated file, João uploads it to this follow-up:

```http
POST /api/v1/portals/p9q8r7.../client/requests/req123.../follow-ups/fu789.../attachments
Authorization: Bearer <citizen-token>
Content-Type: multipart/form-data

name=Planta Baixa Atualizada
file=<binary PDF>
```

The request status automatically moves back to `in_progress` and the workflow resumes.

### 4. Approve and complete

Ana reviews the updated document and approves.

```http
POST /api/v1/portals/p9q8r7.../requests/req123.../tasks/task456.../complete
Authorization: Bearer <ana-token>
Content-Type: application/json

{
  "outcome": "approved",
  "notes": "Documentação completa e em conformidade."
}
```

```json
{
  "id": "task456...",
  "status": "completed",
  "outcome": "approved"
}
```

If this was the final task in the workflow, the request status moves to `completed` and both Ana and João receive a notification.

---

## What's Next

- **Workflows** — configure multi-step approval chains with task dependencies: [Workflows reference](https://portalu.readme.io/reference/getworkflow)
- **Roles & permissions** — create custom roles and assign ABAC scopes: [Portal Roles reference](https://portalu.readme.io/reference/listportalroles)
- **Notification settings** — control who gets notified at each request lifecycle event: [Notification Settings reference](https://portalu.readme.io/reference/getnotificationsettings)
- **Full API reference** — every endpoint: [API Reference](https://portalu.readme.io/reference)
