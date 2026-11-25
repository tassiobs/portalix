import uuid as uuid_module

from fastapi import HTTPException, status
from supabase import acreate_client

from app.core.config import settings

BUCKET = "request-attachments"
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
}
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB


async def _client():
    return await acreate_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


async def upload_file(org_id: str, portal_id: str, content: bytes, filename: str, content_type: str) -> str:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File type not allowed. Accepted: PDF, JPEG, PNG.",
        )
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File too large. Maximum size is 10 MB.",
        )
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    storage_path = f"{org_id}/{portal_id}/{uuid_module.uuid4()}.{ext}"
    client = await _client()
    await client.storage.from_(BUCKET).upload(
        storage_path, content, {"content-type": content_type, "x-upsert": "false"}
    )
    return storage_path


async def create_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    client = await _client()
    result = await client.storage.from_(BUCKET).create_signed_url(storage_path, expires_in)
    return result["signedURL"]
