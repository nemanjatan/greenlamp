"""Speaker resolution + per-client segmentation in a single OpenAI call.

The call is paid coaching ("Write to Freedom"); Scott P. Scheper hosts and
reviews each attending writer's submission. We need to know who each
AssemblyAI speaker label maps to and where each client's segment begins
and ends in the utterance list.
"""

from __future__ import annotations

import os
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, Field

from .transcribe import CallTranscript


class SpeakerResolution(BaseModel):
    speaker_label: str = Field(
        description="AssemblyAI speaker tag exactly as it appears in the transcript (e.g. 'A', 'B')."
    )
    name: str = Field(
        description=(
            "Resolved real name. Use 'Scott P. Scheper' for the host. "
            "If the speaker cannot be confidently identified, use 'Unknown Speaker <label>'."
        )
    )
    role: Literal["host", "client", "other"] = Field(
        description=(
            "'host' for Scott. 'client' for a writer whose submission Scott is reviewing on this call. "
            "'other' for community members who chime in but aren't being reviewed."
        )
    )


class CallSegment(BaseModel):
    client_first_name: str
    client_last_name: str
    client_display_name: str = Field(
        description=(
            "Name as it should appear as a transcript speaker label, e.g. 'Tracy Hawkings' or "
            "'Philip Espinosa, PhD'. Drop credentials if unsure."
        )
    )
    client_speaker_label: str = Field(
        description=(
            "AssemblyAI speaker label of the client, or the literal string 'absent' if Scott "
            "is reviewing the client's submission without them on the call."
        )
    )
    client_question_brief: str = Field(
        description="One-sentence note on what the client asked. Used internally; not the final MD content."
    )
    start_utterance_idx: int = Field(
        description="Inclusive index in the utterance list where this client's segment begins."
    )
    end_utterance_idx: int = Field(
        description="Exclusive index in the utterance list where this client's segment ends."
    )


class CallAnalysis(BaseModel):
    speakers: list[SpeakerResolution]
    segments: list[CallSegment]


_SYSTEM = """\
You analyze a transcribed Zoom call from a paid writing-coaching program called \
"Write to Freedom" run by Scott P. Scheper. Each call has Scott (the host) and \
several community members. On every call Scott reviews a handful of writers' \
submissions one at a time. For each reviewed writer (a "client"), Scott either \
(a) calls them on, pins them, and discusses their work live, or (b) reviews their \
submission while they are absent.

Your job is to produce two things:

1. SPEAKER RESOLUTIONS. For each AssemblyAI speaker label that appears in the \
transcript (A, B, C, ...), state who that person is. The host with the longest \
airtime is Scott P. Scheper. Other speakers are clients or community members. \
Use the chat roster as a candidate set, but you may use names you hear in the \
audio (introductions, when Scott calls someone by name) even if they are not in \
the roster.

2. SEGMENTS. Identify each per-client review block. A block begins when Scott \
introduces, pins, or starts reviewing the client's submission, and ends when he \
wraps up that review and transitions to the next thing (next client, end-of-call \
remarks, an open Q&A). Use the utterance indices as boundaries: \
`start_utterance_idx` is inclusive, `end_utterance_idx` is exclusive. Segments \
must not overlap. If a client is not on the call (Scott reviews them in absentia), \
set `client_speaker_label` to the literal string 'absent'.

BOUNDARIES MUST BE TIGHT. The moment Scott shifts focus to the next client — even \
just to name them, pull up their submission, or read it aloud — that utterance \
belongs to the NEXT segment, not the previous one. Closing pleasantries to the \
finished client (e.g. "thanks Eric, talk to you later") stay with the previous \
segment; everything from "Okay, next up is X..." onward is the new segment.

Output strictly conforms to the schema. Do not include free-form commentary."""


def analyze_call(
    transcript: CallTranscript,
    chat_roster: list[str],
    *,
    api_key: str | None = None,
    model: str = "gpt-4.1",
) -> CallAnalysis:
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to .env or pass api_key explicitly."
        )
    client = OpenAI(api_key=key)

    roster_block = (
        "\n".join(f"- {n}" for n in chat_roster) if chat_roster else "(no chat roster available)"
    )
    user = (
        "## Chat roster (candidate attendee names — incomplete; speakers may not all be in this list)\n\n"
        f"{roster_block}\n\n"
        "## Transcript (one utterance per line, prefixed with [idx] SPEAKER:)\n\n"
        f"{transcript.as_indexed_text()}"
    )

    completion = client.beta.chat.completions.parse(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user},
        ],
        response_format=CallAnalysis,
    )
    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise RuntimeError(
            f"OpenAI segmentation returned no parsed result; refusal={completion.choices[0].message.refusal!r}"
        )
    return parsed
