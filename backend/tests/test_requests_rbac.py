"""
Integration tests for the requests resource RBAC permission enforcement.

All tests use `client` and `auth_headers` fixtures from conftest.py.
The `clean_tables` autouse fixture ensures no shared state between tests.
"""

import uuid

import pytest
import pytest_asyncio


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _invite_and_accept(
    client,
    admin_headers,
    email="member@example.com",
    password="memberpass123",
):
    """Invite a user and accept the invitation; return (user_id, auth_response)."""
    invite_res = await client.post(
        "/api/v1/org/users",
        json={"email": email, "name": "Member"},
        headers=admin_headers,
    )
    assert invite_res.status_code == 201
    inv_token = invite_res.json()["invitation_token"]
    user_id = invite_res.json()["id"]

    accept_res = await client.post(
        "/api/v1/auth/accept-invite",
        json={"token": inv_token, "password": password, "name": "Member"},
    )
    assert accept_res.status_code == 200
    return user_id, accept_res.json()


async def _sign_in(client, email, password):
    """Sign in and return auth headers."""
    res = await client.post(
        "/api/v1/auth/sign-in",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def limited_user_client(client, auth_headers):
    """
    Creates a role with only `requests:read`, invites a user, accepts the invite,
    assigns the role, and returns (client, headers) for that limited user.

    The same `client` instance is returned — only the auth headers differ.
    """
    email = "readonly@example.com"
    password = "readonlypass123"

    # Create a read-only role
    role_res = await client.post(
        "/api/v1/org/roles",
        json={"name": "Read Only", "permissions": ["requests:read"]},
        headers=auth_headers,
    )
    assert role_res.status_code == 201
    role_id = role_res.json()["id"]

    # Invite and accept
    user_id, _ = await _invite_and_accept(client, auth_headers, email=email, password=password)

    # Assign the read-only role
    assign_res = await client.post(
        f"/api/v1/org/users/{user_id}/roles",
        json={"role_id": role_id},
        headers=auth_headers,
    )
    assert assign_res.status_code == 204

    # Sign in as the limited user and return headers
    limited_headers = await _sign_in(client, email, password)
    return client, limited_headers


# ── Tests ─────────────────────────────────────────────────────────────────────

async def test_super_admin_full_access(client, auth_headers):
    """Super admin can perform all CRUD operations on requests."""
    # GET list → 200
    list_res = await client.get("/api/v1/org/requests", headers=auth_headers)
    assert list_res.status_code == 200
    assert isinstance(list_res.json(), list)

    # POST create → 201
    create_res = await client.post(
        "/api/v1/org/requests",
        json={"title": "Test Request"},
        headers=auth_headers,
    )
    assert create_res.status_code == 201
    request_id = create_res.json()["id"]
    assert create_res.json()["title"] == "Test Request"
    assert create_res.json()["status"] == "open"

    # PATCH update → 200
    patch_res = await client.patch(
        f"/api/v1/org/requests/{request_id}",
        json={"title": "Updated Request", "status": "closed"},
        headers=auth_headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Updated Request"
    assert patch_res.json()["status"] == "closed"

    # DELETE → 204
    delete_res = await client.delete(
        f"/api/v1/org/requests/{request_id}",
        headers=auth_headers,
    )
    assert delete_res.status_code == 204


async def test_read_only_can_list(client, auth_headers, limited_user_client):
    """A user with requests:read can GET /org/requests."""
    _, limited_headers = limited_user_client
    res = await client.get("/api/v1/org/requests", headers=limited_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


async def test_read_only_cannot_create(client, auth_headers, limited_user_client):
    """A user with only requests:read cannot POST /org/requests."""
    _, limited_headers = limited_user_client
    res = await client.post(
        "/api/v1/org/requests",
        json={"title": "Forbidden Request"},
        headers=limited_headers,
    )
    assert res.status_code == 403


async def test_read_only_cannot_update(client, auth_headers, limited_user_client):
    """A user with only requests:read cannot PATCH /org/requests/{id}."""
    _, limited_headers = limited_user_client

    # Super admin creates a request first
    create_res = await client.post(
        "/api/v1/org/requests",
        json={"title": "Admin Request"},
        headers=auth_headers,
    )
    assert create_res.status_code == 201
    request_id = create_res.json()["id"]

    res = await client.patch(
        f"/api/v1/org/requests/{request_id}",
        json={"title": "Attempted Update"},
        headers=limited_headers,
    )
    assert res.status_code == 403


async def test_read_only_cannot_delete(client, auth_headers, limited_user_client):
    """A user with only requests:read cannot DELETE /org/requests/{id}."""
    _, limited_headers = limited_user_client

    # Super admin creates a request first
    create_res = await client.post(
        "/api/v1/org/requests",
        json={"title": "Admin Request"},
        headers=auth_headers,
    )
    assert create_res.status_code == 201
    request_id = create_res.json()["id"]

    res = await client.delete(
        f"/api/v1/org/requests/{request_id}",
        headers=limited_headers,
    )
    assert res.status_code == 403


async def test_no_role_cannot_access(client, auth_headers):
    """An invited+accepted user with NO role cannot GET /org/requests."""
    email = "norole@example.com"
    password = "norolepass123"

    _, _ = await _invite_and_accept(client, auth_headers, email=email, password=password)
    norole_headers = await _sign_in(client, email, password)

    res = await client.get("/api/v1/org/requests", headers=norole_headers)
    assert res.status_code == 403


async def test_update_nonexistent_request(client, auth_headers):
    """Super admin PATCH on a random UUID returns 404."""
    random_id = str(uuid.uuid4())
    res = await client.patch(
        f"/api/v1/org/requests/{random_id}",
        json={"title": "Ghost"},
        headers=auth_headers,
    )
    assert res.status_code == 404


async def test_create_and_list_scoped_to_org(client, auth_headers):
    """Create a request and verify it appears in the list with correct fields."""
    create_res = await client.post(
        "/api/v1/org/requests",
        json={"title": "Scoped Request"},
        headers=auth_headers,
    )
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["title"] == "Scoped Request"
    assert created["status"] == "open"
    assert "id" in created
    assert "org_id" in created
    assert "created_by_id" in created
    assert "created_at" in created

    list_res = await client.get("/api/v1/org/requests", headers=auth_headers)
    assert list_res.status_code == 200
    requests = list_res.json()
    assert len(requests) == 1
    assert requests[0]["id"] == created["id"]
    assert requests[0]["title"] == "Scoped Request"
    assert requests[0]["org_id"] == created["org_id"]
    assert requests[0]["created_by_id"] == created["created_by_id"]
