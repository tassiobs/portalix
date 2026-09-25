import resend
from fastapi import HTTPException, status

from app.core.config import settings


def _send(to: str, subject: str, html: str, raise_on_failure: bool = False) -> None:
    if not settings.RESEND_API_KEY:
        return
    try:
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": settings.EMAIL_FROM,
            "to": to,
            "subject": subject,
            "html": html,
        })
    except Exception as e:
        print(f"[email] failed to send to {to}: {e}")
        if raise_on_failure:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to send verification email. Please try again.",
            )


def send_verification_email(to: str, token: str, org_slug: str | None = None, portal_slug: str | None = None) -> None:
    if org_slug and portal_slug:
        url = f"{settings.FRONTEND_URL}/{org_slug}/{portal_slug}/verify-email?token={token}"
    else:
        url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    _send(
        to=to,
        subject="Verify your email",
        html=f'<p>Click the link below to verify your email:</p><p><a href="{url}">{url}</a></p>',
        raise_on_failure=True,
    )


def send_password_reset_email(to: str, token: str, org_slug: str | None = None, portal_slug: str | None = None) -> None:
    if org_slug and portal_slug:
        url = f"{settings.FRONTEND_URL}/{org_slug}/{portal_slug}/reset-password?token={token}"
    else:
        url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    _send(
        to=to,
        subject="Reset your password",
        html=f'<p>Click the link below to reset your password:</p><p><a href="{url}">{url}</a></p>',
    )


def send_invite_email(to: str, token: str, org_name: str) -> None:
    url = f"{settings.FRONTEND_URL}/accept-invite?token={token}"
    _send(
        to=to,
        subject=f"You've been invited to {org_name}",
        html=f'<p>You have been invited to join <strong>{org_name}</strong>.</p><p><a href="{url}">Accept invitation</a></p>',
        raise_on_failure=True,
    )
