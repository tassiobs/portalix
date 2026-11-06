# Getting Started

This guide walks through the complete self-serve setup — from creating your account to having a live citizen-facing portal ready to receive requests.

## Base URL

All API requests are made to:

```
https://portalu-production.up.railway.app
```

---

## Step 1 — Create your org

A single sign-up call creates both your user account and your organization.

```http
POST /api/v1/auth/sign-up
Content-Type: application/json

{
  "org_name": "City of Springfield",
  "name": "Jane Doe",
  "email": "jane@springfield.gov",
  "password": "s3cur3pass!"
}
```

Check your email and verify your account:

```http
POST /api/v1/auth/verify-email
Content-Type: application/json

{ "token": "<token from email>" }
```

{% callout type="warning" title="Verification is required before sign-in" %}
`POST /auth/sign-in` will return an error until the email address is verified. If you're running a bootstrap script that signs up and then immediately signs in, it will fail unless the verification step is completed first. You must handle the verification redirect (or manually verify) before the account is usable.

**`verification_token` is only returned in non-production environments.** On the live API it will not be present in the sign-up response — email verification is the only path. Do not rely on it in production bootstrap scripts.
{% /callout %}

Then sign in to get your access token:

```http
POST /api/v1/auth/sign-in
Content-Type: application/json

{
  "email": "jane@springfield.gov",
  "password": "s3cur3pass!"
}
```

The response includes `access_token` — include it as `Authorization: Bearer <token>` in all subsequent requests.

{% callout type="tip" title="Token Refresh" %}
Access tokens expire. Use `POST /api/v1/auth/refresh` with your `refresh_token` to get a new one.
{% /callout %}

### Optional — set a custom org slug

The org slug appears in every citizen-facing URL (`/citizen/{org_slug}/...`). You can customize it:

```http
PATCH /api/v1/org
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "City of Springfield",
  "slug": "springfield"
}
```

Org slugs are globally unique — you'll get a `409 Conflict` if it's already taken.

{% callout type="warning" title="Treat org slugs as permanent" %}
The org slug is embedded in every citizen-facing URL (`/citizen/{org_slug}/...`). Changing it after citizens have bookmarks, shared links, or integrations pointed at the old slug will break them — there is no redirect. Set the slug you intend to keep before going live.
{% /callout %}

---

## Step 2 — Create a portal

A portal is the citizen-facing surface where users sign up and submit requests. You can have multiple portals per org.

```http
POST /api/v1/org/portals
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Permits & Licenses",
  "slug": "permits",
  "description": "Apply for building permits and business licenses.",
  "domain": "permits.springfield.gov"
}
```

The `slug` is optional — auto-generated from `name` if omitted. Portal slugs are unique within your org.

{% callout type="warning" title="Treat portal slugs as permanent" %}
Like the org slug, the portal slug is part of every citizen URL (`/citizen/{org_slug}/{portal_slug}/...`). Changing it after the portal is live will break existing bookmarks and shared links. Choose your slug before inviting citizens.
{% /callout %}

Once created, citizens can discover the portal at:

```http
GET /api/v1/citizen/springfield/permits
```

This endpoint is public (no auth required) and returns the portal's name, slug, and description — useful for building a landing page before the citizen signs up.

---

## Step 3 — Define request types

Request types are the services your portal offers. Each has a name, optional description, and custom fields.

```http
POST /api/v1/org/portals/{portal_id}/request-types
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Building Permit",
  "description": "Request a permit for construction or renovation."
}
```

Add fields to capture information from citizens:

```http
POST /api/v1/org/portals/{portal_id}/request-types/{rt_id}/fields
Authorization: Bearer <token>
Content-Type: application/json

{
  "label": "Project Description",
  "field_type": "textarea",
  "required": true,
  "order": 0
}
```

Supported field types: `text`, `textarea`, `number`, `date`, `select`.

For `select` fields, `options` must be an array of plain strings — not `{value, label}` objects:

```http
POST /api/v1/org/portals/{portal_id}/request-types/{rt_id}/fields
Authorization: Bearer <token>
Content-Type: application/json

{
  "label": "Property Type",
  "field_type": "select",
  "required": true,
  "order": 1,
  "options": ["Residential", "Commercial", "Industrial"]
}
```

Passing objects (e.g. `{"value": "residential", "label": "Residential"}`) will result in a `422` error.

### Optional — set up a workflow

If requests need review steps, define a workflow:

```http
PUT /api/v1/org/portals/{portal_id}/request-types/{rt_id}/workflow
Authorization: Bearer <token>
Content-Type: application/json

{
  "tasks": [
    {
      "key": "initial_review",
      "name": "Initial Review",
      "assignee_role": "reviewer",
      "deadline_offset_hours": 48
    },
    {
      "key": "final_approval",
      "name": "Final Approval",
      "assignee_role": "approver",
      "depends_on": ["initial_review"]
    }
  ]
}
```

Tasks activate in dependency order and can be assigned to a role or a specific user.

---

## Step 4 — Go live

With the portal and request types in place, your citizen-facing app can:

1. **Show a landing page** — `GET /citizen/{org_slug}/{portal_slug}` (public, no auth)
2. **Let citizens sign up** — `POST /citizen/{org_slug}/{portal_slug}/auth/sign-up`
3. **List available services** — `GET /citizen/{org_slug}/{portal_slug}/request-types`
4. **Accept submissions** — `POST /citizen/{org_slug}/{portal_slug}/requests`

Citizens track their submissions via `GET /citizen/{org_slug}/{portal_slug}/requests`.

---

## What's next

- Invite team members via `POST /org/invitations` and assign them to portals
- Configure lockout and MFA policies via `PATCH /org/settings`
- Monitor and process requests via `GET /org/portals/{portal_id}/requests`
