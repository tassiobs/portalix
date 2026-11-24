from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrgRequestCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200, description="Title of the request", example="New building permit application")


class OrgRequestUpdate(BaseModel):
    title: str | None = Field(None, min_length=2, max_length=200, description="Updated title for the request")
    status: Literal["open", "in_progress", "rejected", "closed"] | None = Field(
        None, description="Updated status for the request"
    )


class OrgRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    created_by_id: UUID
    title: str
    status: str
    created_at: datetime
