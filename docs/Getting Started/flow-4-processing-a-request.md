---
title: "Flow 4 — Processing a Request"
excerpt: List open requests, request clarification from a citizen, and approve to completion.
hidden: false
---

**Who runs this**: an internal user (Ana) with `portal.requests.manage` permission.

**What it covers**: list open requests → complete a task requesting clarification → citizen responds → approve and complete.

---

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
