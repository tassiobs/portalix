# Error Handling

This guide covers the errors your UI will encounter and how to handle each one correctly.

---

## Error format

All errors follow a consistent shape:

```json
{ "detail": "Human-readable message" }
```

Validation errors (`422`) use a structured array:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

`loc` tells you where the error occurred: `body`, `query`, or `path`, followed by the field name.

---

## 401 — Unauthorized

The access token is missing, expired, or invalid.

**Handle by:** silently refreshing the token and retrying the request. If the refresh also fails, redirect to sign-in.

```ts
async function apiFetch(url: string, options: RequestInit) {
  let res = await fetch(url, {
    ...options,
    headers: { ...options.headers, Authorization: `Bearer ${getAccessToken()}` },
  })

  if (res.status === 401) {
    const refreshed = await refreshAccessToken()
    if (!refreshed) {
      redirectToSignIn()
      return
    }
    res = await fetch(url, {
      ...options,
      headers: { ...options.headers, Authorization: `Bearer ${getAccessToken()}` },
    })
  }

  return res
}
```

**Refresh call:**

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{ "refresh_token": "<refresh_token>" }
```

On success, store the new `access_token` and `refresh_token` and retry. On failure (`401` again), clear tokens and send the user to sign-in.

---

## 403 — Forbidden

The user is authenticated but lacks the permission to perform this action.

```json
{ "detail": "You do not have permission to perform this action." }
```

**Handle by:** hiding or disabling the UI element that triggered the call. Do not show a raw "403" — show a message like "You don't have permission to do this."

Use `GET /api/v1/org/portals/permissions` and `GET /api/v1/org/permissions` on load to fetch the user's effective permissions and conditionally render controls before the user ever hits a 403. See the [RBAC for UI](./rbac) guide.

---

## 404 — Not Found

The resource doesn't exist or the user doesn't have access to it (the API returns 404 instead of 403 in some cases to avoid leaking existence).

**Handle by:** showing a "not found" state in the relevant component, not a full-page error.

---

## 409 — Conflict

A uniqueness constraint was violated. Common cases:

| Scenario | Detail message |
|---|---|
| Org slug already taken | `"Org slug already in use"` |
| Portal slug already taken within the org | `"Portal slug already in use within this org"` |
| Domain already in use | `"Domain already in use"` |

**Handle by:** showing an inline error on the relevant field, not a toast or full-page error.

```ts
if (res.status === 409) {
  const { detail } = await res.json()
  setFieldError('slug', detail)
}
```

---

## 422 — Validation Error

A request body field failed validation (missing required field, value out of range, wrong format, etc.).

**Handle by:** mapping `loc` to your form fields and showing inline errors.

```ts
if (res.status === 422) {
  const { detail } = await res.json()
  for (const err of detail) {
    const field = err.loc[err.loc.length - 1] as string
    setFieldError(field, err.msg)
  }
}
```

---

## 500 — Server Error

Something unexpected happened on the server.

**Handle by:** showing a generic "Something went wrong, please try again" message. Do not expose the raw error to the user. Log it for debugging.

---

## Citizen auth errors

The citizen auth flow has a few additional cases:

| Status | Scenario | Handle by |
|---|---|---|
| `401` | Invalid credentials on sign-in | Show "Invalid email or password" on the form |
| `403` | Account locked after too many failed attempts | Show lockout message with duration |
| `404` | Portal or org slug not found | Redirect to a "portal not found" page |
| `409` | Email already registered on this portal | Show "An account with this email already exists" |
