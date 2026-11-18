# Concepts

This page explains the core entities in the Portalu API and how they relate to each other. Understanding the domain model is essential before building any UI on top of the API.

---

## Entity Overview

```
Organization (Org)
├── Org Users (internal staff)
│   └── Roles & Permissions
├── Settings (MFA, lockout policy)
└── Portals
    ├── Request Types
    │   ├── Fields (dynamic form schema)
    │   └── Workflow
    │       └── Task Definitions
    ├── Citizens (end users)
    └── Requests
        ├── Field Values (submitted form data)
        └── Task Instances (active workflow steps)
```

---

## Organization

An **Organization** (org) is the top-level tenant. Every resource belongs to an org. When a developer team signs up, they create an org.

- Identified by a globally unique `slug` (e.g. `springfield`)
- Has org-level settings: lockout policy, MFA requirements, citizen identity scope

## Org User

An **Org User** is an internal staff member — someone working for the org, not a citizen. They authenticate via the standard auth endpoints and act within the org's portals.

Org users have **Roles** that grant **Permissions**. Roles are scoped to either:
- `org` level — applies across the entire org
- `portal` level — applies within a specific portal

Key permissions: `portal.requests:read`, `portal.requests:read_all`, `portal.requests:update`, `portal.workflows:manage`, `portal.users:manage`.

## Portal

A **Portal** is the citizen-facing surface. An org can have multiple portals — one per service line, department, or audience.

- Identified by a `slug` unique within the org (e.g. `permits`)
- Citizens exist within a portal (or shared across the org, depending on `citizen_identity_scope`)
- Has its own request types, workflows, and assigned org users

The full citizen URL pattern is: `/citizen/{org_slug}/{portal_slug}/...`

## Citizen

A **Citizen** is an end user — the person submitting requests through a portal. Citizens authenticate separately from org users, scoped to a specific portal (or org, depending on settings).

Citizens can:
- Sign up, verify email, sign in, refresh tokens
- Browse request types
- Submit and track their own requests

## Request Type

A **Request Type** is a service template — it defines what citizens can apply for (e.g. "Building Permit", "Library Card"). Each portal can have multiple request types.

Each request type has:
- A **name** and optional **description**
- A list of **Fields** that form the submission form
- An optional **Workflow** defining how submissions are processed

## Request Type Field

**Fields** define the dynamic form schema for a request type. When a citizen submits a request, they fill in these fields.

| Field type | UI element |
|---|---|
| `text` | Single-line text input |
| `textarea` | Multi-line text area |
| `number` | Numeric input |
| `date` | Date picker |
| `select` | Dropdown (requires `options` list) |

Fields have `order`, `required`, and optional `options` (for `select` type).

## Request

A **Request** is a citizen's submission against a request type. It contains:
- A reference to its **Request Type**
- The **Field Values** the citizen submitted (keyed to field IDs)
- A `status`: `open` → `in_progress` → `closed` or `rejected`
- A `title` (set by the citizen or defaulted)

## Workflow & Task Definitions

A **Workflow** is attached to a request type and defines the steps required to process a submission. It contains an ordered set of **Task Definitions**.

Each Task Definition specifies:
- A unique `key` within the workflow
- An `assignee_role` or `assignee_user_id` (who handles it)
- `depends_on` — list of task keys that must complete first
- `deadline_offset_hours` — SLA from task activation

Workflows are optional. Requests without a workflow are processed manually.

## Task Instance

When a request is submitted and a workflow is attached, **Task Instances** are created from the Task Definitions. They are the live, actionable items assigned to org users.

Task instances have:
- A `status`: `pending` → `active` → `completed`
- An `outcome` when completed: `approved`, `rejected`, or `clarification_requested`
- `comments` — an audit trail of notes and file attachments

Tasks activate in dependency order — a task only becomes `active` once all tasks in its `depends_on` list are completed.
