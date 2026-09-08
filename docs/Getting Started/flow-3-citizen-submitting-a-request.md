---
title: "Flow 3 — Citizen Submitting a Request"
excerpt: Sign up on a portal, browse request types, stage a file, and submit a request.
hidden: false
---

**Who runs this**: a citizen accessing the portal's client-facing domain.

**What it covers**: sign up → browse request types → stage a file → submit a request.

> **Note**: citizen auth endpoints are scoped to a specific portal. Use `/portals/{portalId}/client/...` — a citizen JWT from one portal cannot be used on another.

---

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

**Next**: [Flow 4 — Processing a Request](./flow-4-processing-a-request)
