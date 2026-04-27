"""Pydantic request/response models for the REST API.

Kept deliberately thin: each model maps 1:1 to a method on the underlying
notebooklm client, and we expose strings/enums rather than full library types
to keep the OpenAPI schema readable.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------- Notebooks ----------

class CreateNotebookRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, examples=["My research notebook"])


class RenameNotebookRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class NotebookOut(BaseModel):
    id: str
    title: str
    created_at: str | None = None
    last_modified: str | None = None


# ---------- Sources ----------

class AddUrlSourceRequest(BaseModel):
    url: str = Field(..., examples=["https://en.wikipedia.org/wiki/Large_language_model"])
    wait: bool = Field(False, description="If true, block until processing completes.")
    wait_timeout: float = Field(120.0, ge=1, le=600)


class AddTextSourceRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)


class SourceOut(BaseModel):
    id: str
    title: str | None = None
    type: str | None = None
    status: str | None = None


# ---------- Chat ----------

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, examples=["Summarise the main argument."])
    source_ids: list[str] | None = None
    conversation_id: str | None = None


class CitationOut(BaseModel):
    source_id: str | None = None
    text: str | None = None
    start: int | None = None
    end: int | None = None


class AskResponse(BaseModel):
    answer: str
    conversation_id: str | None = None
    citations: list[CitationOut] = Field(default_factory=list)


# ---------- Artifacts ----------

class GenerateAudioRequest(BaseModel):
    length: str | None = Field(
        None,
        description="Audio length: SHORT, DEFAULT, or LONG (library enum name).",
        examples=["DEFAULT"],
    )


class ArtifactStatusOut(BaseModel):
    task_id: str | None = None
    status: str | None = None
    artifact_id: str | None = None


class ArtifactOut(BaseModel):
    id: str
    type: str | None = None
    title: str | None = None
    status: str | None = None
