# Building the Citizen UI

This guide maps each citizen-facing screen to the API calls that back it. Use this as a reference when building the public portal experience.

The base path for all citizen endpoints is:
```
/api/v1/citizen/{org_slug}/{portal_slug}
```

---

## Screen 1 — Portal Landing Page

The entry point before a citizen has an account. Show the portal name and description.

**No auth required.**

```http
GET /api/v1/citizen/{org_slug}/{portal_slug}
```

Response:
```json
{
  "name": "Permits & Licenses",
  "slug": "permits",
  "description": "Apply for building permits and business licenses.",
  "org_slug": "springfield"
}
```

Use this to render a branded landing page with a sign-up / sign-in CTA.

---

## Screen 2 — Sign Up

Collect name, email, and password. On success, prompt the citizen to verify their email before they can sign in.

```http
POST /api/v1/citizen/{org_slug}/{portal_slug}/auth/sign-up
Content-Type: application/json

{
  "name": "John Smith",
  "email": "john@example.com",
  "password": "s3cur3pass!"
}
```

The citizen receives a verification email. Surface a message telling them to check their inbox — sign-in will fail until the email is verified, so do not redirect to the sign-in page immediately.

### Email Verification

The verification link in the email contains a token. Your app should handle this as a redirect URL and call:

```http
POST /api/v1/citizen/{org_slug}/{portal_slug}/auth/verify-email
Content-Type: application/json

{ "token": "<token from link>" }
```

After verification, redirect to sign-in.

---

## Screen 3 — Sign In

```http
POST /api/v1/citizen/{org_slug}/{portal_slug}/auth/sign-in
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "s3cur3pass!"
}
```

Response:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

Store both tokens. Use `access_token` as `Authorization: Bearer <token>` on all authenticated requests. When it expires, use the refresh token to get a new one:

```http
POST /api/v1/citizen/{org_slug}/{portal_slug}/auth/refresh
Content-Type: application/json

{ "refresh_token": "<refresh_token>" }
```

### Forgot Password

```http
POST /api/v1/citizen/{org_slug}/{portal_slug}/auth/forgot-password
Content-Type: application/json

{ "email": "john@example.com" }
```

The citizen receives a reset link. Handle the token from that link:

```http
POST /api/v1/citizen/{org_slug}/{portal_slug}/auth/reset-password
Content-Type: application/json

{
  "token": "<token from link>",
  "new_password": "n3wpassword!"
}
```

---

## Screen 4 — Service Catalogue

List the available request types so the citizen can choose what to apply for.

```http
GET /api/v1/citizen/{org_slug}/{portal_slug}/request-types
Authorization: Bearer <token>
```

Response is an array of request types, each including their `fields` array. You have everything needed to render the form on the next screen without an additional API call.

```json
[
  {
    "id": "...",
    "name": "Building Permit",
    "description": "Request a permit for construction or renovation.",
    "fields": [
      { "id": "...", "label": "Project Description", "field_type": "textarea", "required": true, "order": 0 },
      { "id": "...", "label": "Property Type", "field_type": "select", "required": true, "order": 1, "options": ["Residential", "Commercial"] }
    ]
  }
]
```

---

## Screen 5 — Request Submission Form

Render the form dynamically from the `fields` array of the chosen request type.

| `field_type` | Render as |
|---|---|
| `text` | `<input type="text">` |
| `textarea` | `<textarea>` |
| `number` | `<input type="number">` |
| `date` | `<input type="date">` |
| `select` | `<select>` with `options` as `<option>` values |

On submit:

```http
POST /api/v1/citizen/{org_slug}/{portal_slug}/requests
Authorization: Bearer <token>
Content-Type: application/json

{
  "request_type_id": "<rt_id>",
  "title": "Permit for 42 Main St renovation",
  "field_values": [
    { "field_id": "<field_id>", "value": "Full kitchen and bathroom remodel" },
    { "field_id": "<field_id>", "value": "Residential" }
  ]
}
```

On success (`201`), redirect to the request detail screen.

---

## Screen 6 — My Requests (List)

Show all requests submitted by the signed-in citizen.

```http
GET /api/v1/citizen/{org_slug}/{portal_slug}/requests
Authorization: Bearer <token>
```

Each item in the response includes `id`, `title`, `status`, `request_type_name`, and `created_at`. Use `status` to show a badge:

| Status | Meaning |
|---|---|
| `open` | Submitted, not yet reviewed |
| `in_progress` | Being processed |
| `closed` | Completed successfully |
| `rejected` | Declined |

---

## Screen 7 — Request Detail

Show the full submission including submitted field values.

```http
GET /api/v1/citizen/{org_slug}/{portal_slug}/requests/{request_id}
Authorization: Bearer <token>
```

The `field_values` array contains the citizen's answers alongside the field label and type — render them as a read-only summary.

---

## Sign Out

```http
POST /api/v1/citizen/{org_slug}/{portal_slug}/auth/sign-out
Content-Type: application/json

{ "refresh_token": "<refresh_token>" }
```

Clear both tokens from local storage on the client after this call.
