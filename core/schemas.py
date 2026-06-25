from typing import Any, Literal

from pydantic import BaseModel, Field

_VALID_CONTENT_TYPES = Literal["raw_ingestion", "browsing_event", "file_ingest", "explicit_memory"]


class UserInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=50_000)
    embed_text: str | None = Field(default=None, max_length=50_000)
    type: _VALID_CONTENT_TYPES = Field(default="raw_ingestion")
    matter_id: str | None = Field(default=None, max_length=100)
    document_keys: dict | None = Field(default=None)
    created_at: str | None = Field(default=None)
    model: str | None = Field(default=None, max_length=200)
    stream: bool = Field(default=False)


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
