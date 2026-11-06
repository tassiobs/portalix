# Building the Admin UI

This guide maps each internal staff screen to the API calls that back it. Org users (staff, reviewers, admins) use this surface to manage portals, process requests, and handle tasks.

All endpoints require `Authorization: Bearer <access_token>` from the org user auth flow (`POST /api/v1/auth/sign-in`).

---

## Screen 1 — Sign In

```http
POST /api/v1/auth/sign-in
Content-Type: application/json

{
  "email": "jane@springfield.gov",
  "password": "s3cur3pass!"
}
```

Store `access_token` and `refresh_token`. When the access token expires, refresh silently:

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{ "refresh_token": "<refresh_token>" }
```

See the [Error Handling](./error-handling) guide for how to detect expiry and trigger this flow automatically.

---

## Screen 2 — Portal List

The home screen after sign-in. List all portals the user has access to.

```http
GET /api/v1/org/portals
Authorization: Bearer <token>
```

Each portal has `id`, `name`, `slug`, `description`, and `domain`. Use the `id` as the key for all subsequent portal-scoped calls.

---

## Screen 3 — Request Queue

The core admin screen. Shows requests submitted to a portal, with filtering.

```http
GET /api/v1/org/portals/{portal_id}/requests
Authorization: Bearer <token>
```

**Supported query filters:**

| Parameter | Type | Description |
|---|---|---|
| `status` | string | `open`, `in_progress`, `closed`, `rejected` |
| `request_type_id` | UUID | Filter to a specific service type |
| `assigned_to_me` | boolean | Only show requests where I have an active task |
| `from_date` | string | Submissions on or after this date (ISO 8601) |
| `to_date` | string | Submissions on or before this date (ISO 8601) |

**Recommended default view:** `?assigned_to_me=true` for staff with limited permissions, or `?status=open` for admins who have `portal.requests:read_all`.

Use `assigned_to_me=true` as the default for most staff — they only see what's relevant to them without needing elevated permissions.

{% callout type="tip" title="Cross-portal request view" %}
`GET /api/v1/org/requests` (no portal ID) returns requests across all portals in the org. Use this for org-wide dashboards or admin tooling. For portal-specific screens, always use the portal-scoped endpoint above.

`POST /api/v1/org/requests` lets org users submit a request on behalf of a citizen — useful for phone or in-person intake flows where a staff member enters the submission. This is distinct from `POST /citizen/.../requests`, which requires a citizen token and is for self-service submissions.
{% /callout %}

---

## Screen 4 — Request Detail

Full view of a single request including submitted field values, status, and tasks.

```http
GET /api/v1/org/portals/{portal_id}/requests/{request_id}
Authorization: Bearer <token>
```

The response includes `field_values` (the citizen's answers) and basic request metadata. Fetch tasks separately for the workflow panel:

```http
GET /api/v1/org/portals/{portal_id}/requests/{request_id}/tasks
Authorization: Bearer <token>
```

Each task includes its `status`, `assigned_to_user_id`, `deadline`, `outcome`, and `comments`.

### Update request status or title

```http
PATCH /api/v1/org/portals/{portal_id}/requests/{request_id}
Authorization: Bearer <token>
Content-Type: application/json

{ "status": "in_progress" }
```

Valid status values: `open`, `in_progress`, `closed`, `rejected`.

---

## Screen 5 — Task Detail

Staff process a request by completing its tasks in order.

### Reassign a task

```http
PATCH /api/v1/org/portals/{portal_id}/requests/{request_id}/tasks/{task_id}
Authorization: Bearer <token>
Content-Type: application/json

{ "assigned_to_user_id": "<user_id>" }
```

### Add a comment

```http
POST /api/v1/org/portals/{portal_id}/requests/{request_id}/tasks/{task_id}/comments
Authorization: Bearer <token>
Content-Type: application/json

{
  "body": "Documents verified. Proceeding to approval.",
  "file_url": "https://storage.example.com/permit-docs.pdf",
  "file_name": "permit-docs.pdf"
}
```

### Complete a task

```http
POST /api/v1/org/portals/{portal_id}/requests/{request_id}/tasks/{task_id}/complete
Authorization: Bearer <token>
Content-Type: application/json

{
  "outcome": "approved",
  "notes": "All documents verified and approved."
}
```

Valid outcomes: `approved`, `rejected`, `clarification_requested`.

Completing a task activates the next task in the workflow (based on `depends_on`). If no tasks remain, the request can be closed.

---

## Screen 6 — Portal Settings

Manage the portal's name, slug, and domain. Requires `portal.settings:manage`.

```http
PATCH /api/v1/org/portals/{portal_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Permits & Licenses",
  "description": "Updated description.",
  "domain": "permits.springfield.gov"
}
```

---

## Screen 7 — Team Management

### List org users

```http
GET /api/v1/org/users
Authorization: Bearer <token>
```

### Invite a new team member

```http
POST /api/v1/org/invitations
Authorization: Bearer <token>
Content-Type: application/json

{ "email": "newstaff@springfield.gov" }
```

The invitee receives an email with a link to accept and set their password via `POST /api/v1/auth/accept-invite`.

### Assign a user to a portal with a role

```http
POST /api/v1/org/portals/{portal_id}/users
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": "<user_id>",
  "role_id": "<role_id>"
}
```

### Remove a user from a portal

```http
DELETE /api/v1/org/portals/{portal_id}/users/{user_id}
Authorization: Bearer <token>
```

---

## Screen 8 — Request Type Management

Manage the services citizens can apply for. Requires `portal.request_types:manage`.

### List request types

```http
GET /api/v1/org/portals/{portal_id}/request-types
Authorization: Bearer <token>
```

### Create a request type

```http
POST /api/v1/org/portals/{portal_id}/request-types
Authorization: Bearer <token>
Content-Type: application/json

{ "name": "Building Permit", "description": "Apply for a construction permit." }
```

### Add a field

```http
POST /api/v1/org/portals/{portal_id}/request-types/{rt_id}/fields
Authorization: Bearer <token>
Content-Type: application/json

{
  "label": "Property Type",
  "field_type": "select",
  "required": true,
  "order": 0,
  "options": ["Residential", "Commercial", "Industrial"]
}
```

### Configure a workflow

```http
PUT /api/v1/org/portals/{portal_id}/request-types/{rt_id}/workflow
Authorization: Bearer <token>
Content-Type: application/json

{
  "tasks": [
    {
      "key": "review",
      "name": "Initial Review",
      "assignee_role": "reviewer",
      "deadline_offset_hours": 48
    },
    {
      "key": "approval",
      "name": "Final Approval",
      "assignee_role": "approver",
      "depends_on": ["review"]
    }
  ]
}
```

This call is a full replace — resubmit the complete task list each time you update a workflow. The `PUT` overwrites any existing definition.

**Task definition fields:**

| Field | Required | Description |
|---|---|---|
| `key` | Yes | Unique identifier within the workflow (`[a-z0-9_]`) |
| `name` | Yes | Human-readable label shown in the UI |
| `assignee_role` | No | Role name to auto-assign the task to on activation |
| `assignee_user_id` | No | Specific user to assign — takes precedence over `assignee_role` |
| `depends_on` | No | List of task keys that must complete before this task activates |
| `deadline_offset_hours` | No | Hours from activation until the task deadline |
| `fan_out` | No | If `true`, creates one task instance per matching user when multiple users hold the role |

---

## Workflow Lifecycle

This section shows what happens at runtime — from request submission through to completion — so you can build the task panel on the Request Detail screen accurately.

### Step 1 — Request is submitted

When a citizen submits a request for a request type that has a workflow, task instances are created automatically. Tasks with no `depends_on` (or whose dependencies are already met) start as `active`. All others start as `pending`.

For the two-task workflow above, immediately after submission:

```http
GET /api/v1/org/portals/{portal_id}/requests/{request_id}/tasks
Authorization: Bearer <token>
```

```json
[
  {
    "id": "task-instance-1",
    "request_id": "req-abc",
    "status": "active",
    "activated_at": "2026-11-05T10:00:00Z",
    "deadline": "2026-11-07T10:00:00Z",
    "completed_at": null,
    "outcome": null,
    "completion_notes": null,
    "assigned_to_user_id": "user-reviewer",
    "task_definition": {
      "key": "review",
      "name": "Initial Review",
      "depends_on": []
    },
    "comments": []
  },
  {
    "id": "task-instance-2",
    "request_id": "req-abc",
    "status": "pending",
    "activated_at": null,
    "deadline": null,
    "completed_at": null,
    "outcome": null,
    "completion_notes": null,
    "assigned_to_user_id": null,
    "task_definition": {
      "key": "approval",
      "name": "Final Approval",
      "depends_on": ["review"]
    },
    "comments": []
  }
]
```

**Render guidance:** show `active` tasks as actionable cards. Show `pending` tasks as a greyed-out queue so staff can see what's coming without being able to act on them yet.

### Step 2 — Staff complete the first task

```http
POST /api/v1/org/portals/{portal_id}/requests/{request_id}/tasks/{task_id}/complete
Authorization: Bearer <token>
Content-Type: application/json

{
  "outcome": "approved",
  "notes": "All documents verified."
}
```

Valid outcomes: `approved`, `rejected`, `clarification_requested`.

After this call, re-fetch the task list. The `review` task is now `completed` and the `approval` task has become `active`:

```json
[
  {
    "id": "task-instance-1",
    "status": "completed",
    "outcome": "approved",
    "completion_notes": "All documents verified.",
    "completed_at": "2026-11-05T14:30:00Z",
    ...
  },
  {
    "id": "task-instance-2",
    "status": "active",
    "activated_at": "2026-11-05T14:30:00Z",
    "deadline": null,
    "outcome": null,
    ...
  }
]
```

### Step 3 — All tasks complete

Once the final task is completed, the request is not automatically closed — your UI should prompt the staff member to update the request status to `closed` or `rejected` based on the overall outcome:

```http
PATCH /api/v1/org/portals/{portal_id}/requests/{request_id}
Authorization: Bearer <token>
Content-Type: application/json

{ "status": "closed" }
```

### Fan-out tasks

If a task definition has `fan_out: true` and multiple users hold the `assignee_role`, one task instance is created per matching user. All fan-out instances must be completed before downstream tasks activate. Use this for parallel review steps (e.g. two independent approvals required before escalation).

### Requests without a workflow

If a request type has no workflow, `GET .../tasks` returns an empty array. Status updates are entirely manual via `PATCH .../requests/{id}`.
