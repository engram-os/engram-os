from pydantic import BaseModel
from typing import Any


class ChatResponse(BaseModel):
    reply: str
    context_used: list[Any]


class IngestResponse(BaseModel):
    status: str
    id: str | None = None
    score: float | None = None


class AuditVerifyResponse(BaseModel):
    valid: bool
    entries_checked: int | None = None
    first_failed_id: int | None = None
    error: str | None = None
