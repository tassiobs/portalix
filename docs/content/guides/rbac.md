# RBAC for UI

This guide explains how to use the permissions system to conditionally show, hide, or disable UI elements based on what the current user is allowed to do.

---

## How permissions work

Permissions are attached to **roles**, and roles are assigned to users at two levels:

- **Org level** — applies across the entire org (e.g. ability to manage users or create portals)
- **Portal level** — applies within a specific portal (e.g. ability to view requests or manage workflows)

A user can have multiple roles at both levels simultaneously.

---

## Fetching permissions on load

Fetch the user's effective permissions once after sign-in and store them in your app state. There are two endpoints:

**Org-level permissions:**
```http
GET /api/v1/org/permissions
Authorization: Bearer <token>
```

**Portal-level permissions** (per portal):
```http
GET /api/v1/org/portals/permissions
Authorization: Bearer <token>
```

This returns all defined permission keys with labels and descriptions — use it to build your permission map.

To see what roles (and therefore permissions) a specific user has:
```http
GET /api/v1/org/users/{user_id}/roles
Authorization: Bearer <token>
```

---

## Permission reference

### Org-level permissions

| Key | Label | Controls |
|---|---|---|
| `org.users.manage` | Manage Users | Invite users, assign org roles, deactivate accounts |
| `org.portals.manage` | Manage Portals | Create and delete portals |
| `requests:read` | View Requests | View org-level requests |
| `requests:create` | Create Requests | Submit new org-level requests |
| `requests:update` | Update Requests | Update status or title of org-level requests |
| `requests:delete` | Delete Requests | Delete org-level requests |

### Portal-level permissions

| Key | Label | Controls |
|---|---|---|
| `portal.requests:read` | View Assigned Requests | See requests where the user has a task assigned |
| `portal.requests:read_all` | View All Requests | See every request on the portal regardless of assignment |
| `portal.requests:update` | Update Requests | Change request status or title; complete tasks |
| `portal.request_types:manage` | Manage Request Types | Create/edit/delete request types and their fields |
| `portal.users:manage` | Manage Portal Users | Assign and remove users from the portal |
| `portal.settings:manage` | Manage Portal Settings | Edit portal name, slug, description, domain |
| `portal.workflows:view` | View Workflows | Read workflow definitions |
| `portal.workflows:manage` | Manage Workflows | Create and update workflow definitions |

---

## Pattern: permission-aware rendering

The recommended pattern is to resolve permissions once and inject them via context, then gate UI elements at the component level.

```ts
// After sign-in, fetch and store resolved permissions
const myRoles = await fetch('/api/v1/org/users/me/roles', { headers })
const permissions = new Set(myRoles.flatMap(r => r.permissions))

// Then in components:
{permissions.has('org.users.manage') && <InviteUserButton />}
{permissions.has('portal.requests:read_all') && <AllRequestsTab />}
```

---

## Common UI gating examples

### Show "Invite User" button
```ts
permissions.has('org.users.manage')
```

### Show "Create Portal" button
```ts
permissions.has('org.portals.manage')
```

### Show "All Requests" tab vs "My Tasks" only
```ts
permissions.has('portal.requests:read_all')
  ? showAllRequestsTab()
  : showMyTasksTab()
```

### Show "Manage Workflow" option on a request type
```ts
permissions.has('portal.workflows:manage')
```

### Show "Complete Task" button
```ts
permissions.has('portal.requests:update')
```

### Show portal settings link
```ts
permissions.has('portal.settings:manage')
```

---

## Roles setup

Roles are created per org and then assigned to users. To set up roles:

### Create a portal-level role
```http
POST /api/v1/org/roles
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Reviewer",
  "level": "portal",
  "permissions": ["portal.requests:read", "portal.requests:update"]
}
```

### Assign the role to a user on a portal
```http
POST /api/v1/org/portals/{portal_id}/users
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": "<user_id>",
  "role_id": "<role_id>"
}
```

### Assign an org-level role to a user
```http
POST /api/v1/org/users/{user_id}/roles
Authorization: Bearer <token>
Content-Type: application/json

{ "role_id": "<role_id>" }
```

---

## Important: server-side enforcement

Permissions are enforced on the server — the API will return `403` if a user attempts an action they lack permission for. UI gating is for usability (hiding irrelevant controls), not security. Always rely on the API's enforcement as the source of truth.
