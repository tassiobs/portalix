"""
Integration tests for RBAC role management flows.

All tests use `client`, `registered_org`, and `auth_headers` fixtures from
conftest.py. The `clean_tables` autouse fixture ensures no shared state.
"""

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _create_role(client, headers, name="Reviewer", permissions=None):
    if permissions is None:
        permissions = ["org.portals.manage"]
    return await client.post(
        "/api/v1/org/roles",
        json={"name": name, "permissions": permissions},
        headers=headers,
    )


async def _invite_and_accept(client, admin_headers,
                              email="member@example.com",
                              password="memberpass123"):
    """Invite a user and accept the invitation; return the accepted auth response."""
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


# ── Tests ─────────────────────────────────────────────────────────────────────

async def test_list_default_roles(client, auth_headers):
    """After signup → GET /org/roles → Super Admin role is present."""
    res = await client.get("/api/v1/org/roles", headers=auth_headers)
    assert res.status_code == 200
    roles = res.json()
    assert isinstance(roles, list)
    names = [r["name"] for r in roles]
    assert "Super Admin" in names
    # Super Admin should be marked as default
    super_admin = next(r for r in roles if r["name"] == "Super Admin")
    assert super_admin["is_default"] is True


async def test_create_role(client, auth_headers):
    """Create a 'Reviewer' role with org.portals.manage permission → 201."""
    res = await _create_role(client, auth_headers, name="Reviewer",
                              permissions=["org.portals.manage"])
    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "Reviewer"
    assert "org.portals.manage" in body["permissions"]
    assert body["is_default"] is False
    assert "id" in body


async def test_create_role_invalid_permission(client, auth_headers):
    """Create role with a nonexistent permission → 422."""
    res = await _create_role(client, auth_headers, name="BadRole",
                              permissions=["org.nonexistent.permission"])
    assert res.status_code == 422


async def test_update_role(client, auth_headers):
    """Create role → update name → role name is updated."""
    create_res = await _create_role(client, auth_headers)
    assert create_res.status_code == 201
    role_id = create_res.json()["id"]

    update_res = await client.patch(
        f"/api/v1/org/roles/{role_id}",
        json={"name": "Senior Reviewer"},
        headers=auth_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Senior Reviewer"

    # Confirm via GET
    get_res = await client.get(f"/api/v1/org/roles/{role_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Senior Reviewer"


async def test_delete_role(client, auth_headers):
    """Create role → delete → role is no longer in list."""
    create_res = await _create_role(client, auth_headers)
    role_id = create_res.json()["id"]

    delete_res = await client.delete(
        f"/api/v1/org/roles/{role_id}",
        headers=auth_headers,
    )
    assert delete_res.status_code == 204

    list_res = await client.get("/api/v1/org/roles", headers=auth_headers)
    role_ids = [r["id"] for r in list_res.json()]
    assert role_id not in role_ids


async def test_cannot_delete_default_role(client, auth_headers):
    """Try to delete Super Admin (is_default=True) → 409."""
    list_res = await client.get("/api/v1/org/roles", headers=auth_headers)
    roles = list_res.json()
    super_admin = next(r for r in roles if r["name"] == "Super Admin")
    role_id = super_admin["id"]

    delete_res = await client.delete(
        f"/api/v1/org/roles/{role_id}",
        headers=auth_headers,
    )
    assert delete_res.status_code == 409


async def test_assign_role_to_user(client, auth_headers):
    """Invite user → accept → assign role → user has the role."""
    # Create a custom role
    role_res = await _create_role(client, auth_headers)
    role_id = role_res.json()["id"]

    # Invite and accept
    user_id, _ = await _invite_and_accept(client, auth_headers)

    # Assign role
    assign_res = await client.post(
        f"/api/v1/org/users/{user_id}/roles",
        json={"role_id": role_id},
        headers=auth_headers,
    )
    assert assign_res.status_code == 204

    # Verify user has the role
    roles_res = await client.get(
        f"/api/v1/org/users/{user_id}/roles",
        headers=auth_headers,
    )
    assert roles_res.status_code == 200
    user_role_ids = [r["id"] for r in roles_res.json()]
    assert role_id in user_role_ids


async def test_remove_role_from_user(client, auth_headers):
    """Assign role → remove role → user has no custom roles."""
    role_res = await _create_role(client, auth_headers)
    role_id = role_res.json()["id"]

    user_id, _ = await _invite_and_accept(client, auth_headers)

    # Assign
    await client.post(
        f"/api/v1/org/users/{user_id}/roles",
        json={"role_id": role_id},
        headers=auth_headers,
    )

    # Remove
    remove_res = await client.delete(
        f"/api/v1/org/users/{user_id}/roles/{role_id}",
        headers=auth_headers,
    )
    assert remove_res.status_code == 204

    # Verify role is gone
    roles_res = await client.get(
        f"/api/v1/org/users/{user_id}/roles",
        headers=auth_headers,
    )
    user_role_ids = [r["id"] for r in roles_res.json()]
    assert role_id not in user_role_ids


async def test_list_user_roles(client, auth_headers):
    """Assign 2 roles → GET /org/users/{id}/roles → both listed."""
    role1_res = await _create_role(client, auth_headers, name="Role One",
                                    permissions=["org.portals.manage"])
    role2_res = await _create_role(client, auth_headers, name="Role Two",
                                    permissions=["org.users.manage"])
    role1_id = role1_res.json()["id"]
    role2_id = role2_res.json()["id"]

    user_id, _ = await _invite_and_accept(client, auth_headers)

    await client.post(
        f"/api/v1/org/users/{user_id}/roles",
        json={"role_id": role1_id},
        headers=auth_headers,
    )
    await client.post(
        f"/api/v1/org/users/{user_id}/roles",
        json={"role_id": role2_id},
        headers=auth_headers,
    )

    roles_res = await client.get(
        f"/api/v1/org/users/{user_id}/roles",
        headers=auth_headers,
    )
    assert roles_res.status_code == 200
    user_role_ids = {r["id"] for r in roles_res.json()}
    assert role1_id in user_role_ids
    assert role2_id in user_role_ids


async def test_permission_enforced(client, auth_headers, registered_org):
    """
    Invite user (no extra roles) → try GET /org/users → still allowed (any active user can list);
    the permission guard is on org.users.manage sensitive operations, but list_users is open to
    any authenticated active user. Instead, test that creating a user (which requires
    org.users.manage) is forbidden for the uninvited user, then assign the role and retry → 200.
    """
    # Invite and accept a plain user (no extra roles beyond default invited state)
    user_id, member_auth = await _invite_and_accept(client, auth_headers,
                                                     email="member@example.com")
    member_token = member_auth["access_token"]
    member_headers = {"Authorization": f"Bearer {member_token}"}

    # Plain member trying to invite someone (requires org.users.manage) → 403
    forbidden_res = await client.post(
        "/api/v1/org/users",
        json={"email": "another@example.com"},
        headers=member_headers,
    )
    assert forbidden_res.status_code == 403

    # Admin creates a role with org.users.manage and assigns it to the member
    role_res = await _create_role(client, auth_headers, name="Manager",
                                   permissions=["org.users.manage"])
    role_id = role_res.json()["id"]
    await client.post(
        f"/api/v1/org/users/{user_id}/roles",
        json={"role_id": role_id},
        headers=auth_headers,
    )

    # Member now re-signs in to get a fresh token (token doesn't change, but DB check does)
    # Actually, the permission check is done at request time via DB — retry with same token
    allowed_res = await client.post(
        "/api/v1/org/users",
        json={"email": "another@example.com"},
        headers=member_headers,
    )
    assert allowed_res.status_code == 201
