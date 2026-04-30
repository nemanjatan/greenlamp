"""Public-facing API schemas (Pydantic) — what the frontend sees."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class JobStage(str, Enum):
    queued = "queued"
    transcribing = "transcribing"
    cleaning = "cleaning"
    segmenting = "segmenting"
    enriching = "enriching"
    uploading = "uploading"
    complete = "complete"
    failed = "failed"


class JobResultDTO(BaseModel):
    client_first_name: str
    client_last_name: str
    client_display_name: str
    filename: str
    markdown: str  # full MD text inlined so the FE can render without a second fetch
    cdn_url: str  # uploadcare CDN URL for direct download
    topics: list[str]


class JobDTO(BaseModel):
    id: str
    stage: JobStage
    progress_pct: int
    audio_filename: str
    duration_ms: int
    utterance_count: int
    segments_count: int
    results: list[JobResultDTO]
    zip_url: str | None
    error: str | None
    started_at: float | None
    finished_at: float | None


class CreateJobRequest(BaseModel):
    audio_url: str  # Uploadcare CDN URL of the uploaded MP4/M4A
    filename: str


class CreateJobResponse(BaseModel):
    id: str


class LoginRequest(BaseModel):
    password: str


class AuthCheckResponse(BaseModel):
    authenticated: bool
