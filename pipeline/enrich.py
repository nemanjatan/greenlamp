"""Generate Client Question + Distilled Advice + Key Principles + Topics for one client segment."""

from __future__ import annotations

import os

from openai import OpenAI
from pydantic import BaseModel, Field


class SegmentEnrichment(BaseModel):
    client_question: str = Field(
        description=(
            "Faithful one- or two-sentence rendering of the client's question, in whichever "
            "voice (first- or third-person) reads most naturally. Preserve specifics."
        )
    )
    distilled_advice: list[str] = Field(
        description=(
            "6 to 12 concrete, actionable advice bullets distilled from Scott's response. Each "
            "bullet is one specific recommendation."
        )
    )
    key_principles: list[str] = Field(
        description=(
            "5 to 10 broader principles or maxims surfaced in the response, expressed at a "
            "higher level than the advice items."
        )
    )
    topics: list[str] = Field(
        description="4 to 8 short topical tags (lowercase, 1-3 words each)."
    )


_SYSTEM = """\
You are summarizing one client's Q&A segment from a writing-coaching Zoom call \
hosted by Scott P. Scheper. The transcript may include Scott's introduction of \
the client and his transition out of the segment.

Produce four artifacts, all derived strictly from the transcript:

1. CLIENT_QUESTION: a one- or two-sentence rendering of what the client is asking \
about. Use whichever voice (first- or third-person) reads most naturally. Keep \
the specifics that matter.

2. DISTILLED_ADVICE: 6-12 concrete, actionable bullets. Each bullet is ONE \
specific recommendation Scott gave. Drop filler. Match the conciseness of \
strong examples (e.g., "Use $14.95 with a higher 'retail' anchor price").

3. KEY_PRINCIPLES: 5-10 higher-level maxims surfaced in Scott's response, \
broader than the advice items (e.g., "Price anchoring increases perceived value").

4. TOPICS: 4-8 short topical tags, lowercase, 1-3 words each \
(e.g., "pricing strategy", "currency selection").

Do not invent content. Do not include conversational filler. Output strictly \
conforms to the schema."""


def enrich_segment(
    segment_transcript: str,
    *,
    api_key: str | None = None,
    model: str = "gpt-4.1",
) -> SegmentEnrichment:
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to .env or pass api_key explicitly."
        )
    client = OpenAI(api_key=key)
    completion = client.beta.chat.completions.parse(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": segment_transcript},
        ],
        response_format=SegmentEnrichment,
    )
    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise RuntimeError(
            f"OpenAI enrichment returned no parsed result; refusal={completion.choices[0].message.refusal!r}"
        )
    return parsed
