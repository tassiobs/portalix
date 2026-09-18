from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RequestCreate(BaseModel):
    title: str


class RequestUpdate(BaseModel):
    title: str | None = None
    status: str | None = None


class RequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    created_by_id: UUID
    title: str
    status: str
    created_at: datetime
