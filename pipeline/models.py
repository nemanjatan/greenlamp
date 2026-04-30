from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

ContentType = Literal["Zoom Response", "Email Response", "Loom Response"]


class TranscriptTurn(BaseModel):
    speaker: str
    text: str


class ClientResponseDoc(BaseModel):
    """One per-client output document, mapping 1:1 to the markdown template."""

    call_date: date
    client_first_name: str
    client_last_name: str
    client_display_name: str = Field(
        description="Speaker label as used in the transcript, may include credentials (e.g. 'Philip Espinosa, PhD')."
    )
    program: str = "Write to Freedom"
    content_type: ContentType = "Zoom Response"
    topics: list[str]
    client_question: str
    distilled_advice: list[str]
    key_principles: list[str]
    transcript: list[TranscriptTurn]

    def slug(self) -> str:
        last = _slugify(self.client_last_name)
        first = _slugify(self.client_first_name)
        # Drop placeholder/empty name parts so we never emit "_-robin" or
        # "_unknown-christoph"-style filenames.
        parts = [p for p in (last, first) if p and p != "unknown"]
        slug_tail = "-".join(parts) if parts else "unknown"
        return f"wtf_zoom-response_{self.call_date.isoformat()}_{slug_tail}"

    def filename(self) -> str:
        return f"{self.slug()}.md"


class CallSegment(BaseModel):
    """Output of the segmentation LLM pass for one client block within a call."""

    client_display_name: str
    client_first_name: str
    client_last_name: str
    client_question: str
    transcript_start_idx: int = Field(
        description="Index into the per-utterance list where this client's segment begins (inclusive)."
    )
    transcript_end_idx: int = Field(
        description="Index where this client's segment ends (exclusive)."
    )


class CallSegmentation(BaseModel):
    """Segmentation output for an entire call."""

    segments: list[CallSegment]


def _slugify(name: str) -> str:
    return "".join(c.lower() if c.isalnum() else "" for c in name)
