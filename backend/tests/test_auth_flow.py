"""
Integration tests for authentication flows.

Each test is fully self-contained. The `clean_tables` fixture (autouse) in
conftest.py truncates all tables between tests, so there is no shared state.
"""

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _sign_up(client, email="user@example.com", password="secret123",
                   name="Test User", org_name="Test Org"):
    res = await client.post("/api/v1/auth/sign-up", json={
        "email": email,
        "password": password,
        "name": name,
        "org_name": org_name,
    })
    return res


async def _verify(client, token):
    return await client.post("/api/v1/auth/verify-email", json={"token": token})


async def _sign_in(client, email, password):
    return await client.post("/api/v1/auth/sign-in", json={
        "email": email,
        "password": password,
    })


# ── Tests ─────────────────────────────────────────────────────────────────────

async def test_full_signup_and_verify(client):
    """Sign up → verify email → response has email_verified=True and roles assigned."""
    signup_res = await _sign_up(client)
    assert signup_res.status_code == 201
    body = signup_res.json()
    assert "verification_token" in body
    assert body["user"]["email_verified"] is False

    verify_res = await _verify(client, body["verification_token"])
    assert verify_res.status_code == 200
    data = verify_res.json()
    assert data["user"]["email_verified"] is True
    assert data["user"]["email"] == "user@example.com"
    # Super Admin role should be assigned
    assert len(data["user"]["org_roles"]) >= 1
    assert any(r["name"] == "Super Admin" for r in data["user"]["org_roles"])
    assert "access_token" in data
    assert "refresh_token" in data


async def test_cannot_signin_before_verify(client):
    """Sign up without verifying email → sign in should return 403."""
    await _sign_up(client)
    res = await _sign_in(client, "user@example.com", "secret123")
    assert res.status_code == 403


async def test_signin_after_verify(client):
    """Sign up → verify → sign in → returns valid tokens."""
    signup_res = await _sign_up(client)
    token = signup_res.json()["verification_token"]
    await _verify(client, token)

    signin_res = await _sign_in(client, "user@example.com", "secret123")
    assert signin_res.status_code == 200
    data = signin_res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "user@example.com"


async def test_get_me(client):
    """Sign up → verify → GET /auth/me → returns correct user data."""
    signup_res = await _sign_up(client)
    token = signup_res.json()["verification_token"]
    auth = await _verify(client, token)
    access_token = auth.json()["access_token"]

    res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "user@example.com"
    assert data["name"] == "Test User"
    assert data["email_verified"] is True
    assert data["status"] == "active"


async def test_update_me(client):
    """Sign up → verify → PATCH /auth/me with new name → verify name updated."""
    signup_res = await _sign_up(client)
    token = signup_res.json()["verification_token"]
    auth = await _verify(client, token)
    access_token = auth.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    patch_res = await client.patch(
        "/api/v1/auth/me",
        json={"name": "Updated Name"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Updated Name"

    # Confirm persistence
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["name"] == "Updated Name"


async def test_forgot_and_reset_password(client):
    """
    Sign up → verify → forgot-password → reset-password →
    sign in with new password → 200;
    sign in with old password → 401.
    """
    signup_res = await _sign_up(client)
    token = signup_res.json()["verification_token"]
    await _verify(client, token)

    # Forgot password
    forgot_res = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "user@example.com"},
    )
    assert forgot_res.status_code == 200
    reset_token = forgot_res.json()["reset_token"]
    assert reset_token  # must not be empty

    # Reset password
    reset_res = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "newpassword456"},
    )
    assert reset_res.status_code == 204

    # Sign in with new password
    new_signin = await _sign_in(client, "user@example.com", "newpassword456")
    assert new_signin.status_code == 200

    # Sign in with old password should fail
    old_signin = await _sign_in(client, "user@example.com", "secret123")
    assert old_signin.status_code == 401


async def test_reset_password_token_single_use(client):
    """Use the same reset token twice → second use returns 400."""
    signup_res = await _sign_up(client)
    token = signup_res.json()["verification_token"]
    await _verify(client, token)

    forgot_res = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "user@example.com"},
    )
    reset_token = forgot_res.json()["reset_token"]

    # First use succeeds
    res1 = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "firstnewpass"},
    )
    assert res1.status_code == 204

    # Second use rejected
    res2 = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "secondnewpass"},
    )
    assert res2.status_code == 400


async def test_refresh_token(client):
    """Sign in → refresh → get new access token → old refresh token rejected."""
    signup_res = await _sign_up(client)
    token = signup_res.json()["verification_token"]
    await _verify(client, token)

    signin_res = await _sign_in(client, "user@example.com", "secret123")
    old_refresh = signin_res.json()["refresh_token"]

    # Refresh
    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["refresh_token"] != old_refresh

    # Old refresh token should now be rejected (rotation)
    stale_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert stale_res.status_code == 401


async def test_signout_invalidates_refresh(client):
    """Sign in → sign out → try refresh with old token → 401."""
    signup_res = await _sign_up(client)
    token = signup_res.json()["verification_token"]
    await _verify(client, token)

    signin_res = await _sign_in(client, "user@example.com", "secret123")
    refresh_token = signin_res.json()["refresh_token"]

    # Sign out
    signout_res = await client.post(
        "/api/v1/auth/sign-out",
        json={"refresh_token": refresh_token},
    )
    assert signout_res.status_code == 204

    # Refresh attempt should fail
    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 401


async def test_sessions_listed_after_signin(client):
    """Sign in twice → GET /auth/sessions → at least 2 sessions returned."""
    signup_res = await _sign_up(client)
    token = signup_res.json()["verification_token"]
    await _verify(client, token)

    signin1 = await _sign_in(client, "user@example.com", "secret123")
    access_token1 = signin1.json()["access_token"]

    signin2 = await _sign_in(client, "user@example.com", "secret123")
    access_token2 = signin2.json()["access_token"]

    sessions_res = await client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {access_token2}"},
    )
    assert sessions_res.status_code == 200
    sessions = sessions_res.json()
    assert isinstance(sessions, list)
    assert len(sessions) >= 2


async def test_resend_verification(client):
    """Sign up → resend-verification → get new token → verify with new token → 200."""
    signup_res = await _sign_up(client)
    original_token = signup_res.json()["verification_token"]

    # Resend
    resend_res = await client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "user@example.com"},
    )
    assert resend_res.status_code == 200
    new_token = resend_res.json().get("verification_token")
    assert new_token
    assert new_token != original_token

    # Verify with new token
    verify_res = await _verify(client, new_token)
    assert verify_res.status_code == 200
    assert verify_res.json()["user"]["email_verified"] is True
