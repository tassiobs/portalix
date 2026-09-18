"""
Integration tests for invitation flows.

All tests use `client`, `registered_org`, and `auth_headers` fixtures from
conftest.py. The `clean_tables` autouse fixture ensures no shared state.
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select, update

from app.db.models.user import InvitationToken
from tests.conftest import TestSessionLocal


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _invite_user(client, headers, email="invited@example.com", name="Invited"):
    """POST /org/users to invite a new user, return the full response."""
    return await client.post(
        "/api/v1/org/users",
        json={"email": email, "name": name},
        headers=headers,
    )


async def _accept_invite(client, token, password="invitedpass123", name=None):
    payload = {"token": token, "password": password}
    if name:
        payload["name"] = name
    return await client.post("/api/v1/auth/accept-invite", json=payload)


# ── Tests ─────────────────────────────────────────────────────────────────────

async def test_invite_user(client, auth_headers):
    """Admin invites user → response contains invitation_token."""
    res = await _invite_user(client, auth_headers)
    assert res.status_code == 201
    body = res.json()
    assert "invitation_token" in body
    assert body["email"] == "invited@example.com"
    assert body["status"] == "active"


async def test_accept_invite(client, auth_headers):
    """Admin invites → invited user accepts with password → gets valid access token."""
    invite_res = await _invite_user(client, auth_headers)
    assert invite_res.status_code == 201
    inv_token = invite_res.json()["invitation_token"]

    accept_res = await _accept_invite(client, inv_token, name="New Member")
    assert accept_res.status_code == 200
    data = accept_res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "invited@example.com"
    assert data["user"]["email_verified"] is True
    assert data["user"]["name"] == "New Member"


async def test_accept_invite_token_single_use(client, auth_headers):
    """Accept same invite twice → second returns 400 (invitation no longer pending)."""
    invite_res = await _invite_user(client, auth_headers)
    inv_token = invite_res.json()["invitation_token"]

    first = await _accept_invite(client, inv_token)
    assert first.status_code == 200

    second = await _accept_invite(client, inv_token, password="differentpass")
    assert second.status_code == 400


async def test_expired_invite_rejected(client, auth_headers):
    """Create invite, manually set expires_at in past via DB → accept → 400."""
    invite_res = await _invite_user(client, auth_headers)
    assert invite_res.status_code == 201
    inv_token_value = invite_res.json()["invitation_token"]

    # Manually expire the invitation via direct DB access
    async with TestSessionLocal() as session:
        result = await session.execute(
            select(InvitationToken).where(InvitationToken.token == inv_token_value)
        )
        inv = result.scalar_one()
        inv.expires_at = datetime.utcnow() - timedelta(days=1)
        await session.commit()

    accept_res = await _accept_invite(client, inv_token_value)
    assert accept_res.status_code == 400


async def test_list_invitations(client, auth_headers):
    """Invite 2 users → GET /org/invitations → both listed with status=pending."""
    await _invite_user(client, auth_headers, email="user1@example.com")
    await _invite_user(client, auth_headers, email="user2@example.com")

    res = await client.get("/api/v1/org/invitations", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "data" in data
    invitations = data["data"]
    assert len(invitations) == 2
    emails = {inv["email"] for inv in invitations}
    assert "user1@example.com" in emails
    assert "user2@example.com" in emails
    for inv in invitations:
        assert inv["status"] == "pending"


async def test_invitation_status_accepted_after_accept(client, auth_headers):
    """Invite → accept → GET /org/invitations → invitation has status=accepted."""
    invite_res = await _invite_user(client, auth_headers)
    inv_token = invite_res.json()["invitation_token"]
    invited_user_id = invite_res.json()["id"]

    accept_res = await _accept_invite(client, inv_token)
    assert accept_res.status_code == 200

    list_res = await client.get("/api/v1/org/invitations", headers=auth_headers)
    assert list_res.status_code == 200
    invitations = list_res.json()["data"]
    assert len(invitations) == 1
    assert invitations[0]["status"] == "accepted"
    assert invitations[0]["accepted_at"] is not None


async def test_cancel_invitation(client, auth_headers):
    """Invite → cancel → invitation has status=cancelled in list."""
    invite_res = await _invite_user(client, auth_headers)
    inv_id = invite_res.json()["id"]

    # Find invitation id from list
    list_res = await client.get("/api/v1/org/invitations", headers=auth_headers)
    invitations = list_res.json()["data"]
    assert len(invitations) == 1
    invitation_id = invitations[0]["id"]

    cancel_res = await client.post(
        f"/api/v1/org/invitations/{invitation_id}/cancel",
        headers=auth_headers,
    )
    assert cancel_res.status_code == 204

    list_res2 = await client.get("/api/v1/org/invitations", headers=auth_headers)
    invitations2 = list_res2.json()["data"]
    assert invitations2[0]["status"] == "cancelled"


async def test_cancelled_invite_cannot_be_accepted(client, auth_headers):
    """Invite → cancel → try accept → 400 (invitation not pending)."""
    invite_res = await _invite_user(client, auth_headers)
    inv_token = invite_res.json()["invitation_token"]

    # Get invitation id and cancel
    list_res = await client.get("/api/v1/org/invitations", headers=auth_headers)
    invitation_id = list_res.json()["data"][0]["id"]
    await client.post(
        f"/api/v1/org/invitations/{invitation_id}/cancel",
        headers=auth_headers,
    )

    accept_res = await _accept_invite(client, inv_token)
    assert accept_res.status_code == 400


async def test_resend_invitation(client, auth_headers):
    """Invite → resend → old token rejected on accept, new token works."""
    invite_res = await _invite_user(client, auth_headers)
    old_token = invite_res.json()["invitation_token"]

    # Find invitation id
    list_res = await client.get("/api/v1/org/invitations", headers=auth_headers)
    invitation_id = list_res.json()["data"][0]["id"]

    # Resend
    resend_res = await client.post(
        f"/api/v1/org/invitations/{invitation_id}/resend",
        headers=auth_headers,
    )
    assert resend_res.status_code == 200
    new_token = resend_res.json()["invitation_token"]
    assert new_token != old_token

    # Old token should be rejected
    old_accept = await _accept_invite(client, old_token)
    assert old_accept.status_code == 400

    # New token should work
    new_accept = await _accept_invite(client, new_token)
    assert new_accept.status_code == 200
