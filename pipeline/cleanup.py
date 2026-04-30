"""Post-AssemblyAI utterance cleanup.

Two transformations, both run before segmentation:

1. **Microburst merging** — AssemblyAI's diarizer occasionally flips speakers for
   1-3 words mid-monologue ("we", "how" inside a long Scott block). When a short
   utterance is sandwiched between two same-speaker utterances by a different
   speaker, fold it back into the surrounding block.

2. **Long-utterance splitting** — Scott's monologues at segment transitions
   (covering one client's wrap-up, introducing the next, then reading their
   submission) come back as a single 5-15 minute utterance. The segmentation
   LLM can only draw boundaries between utterances, so we split long ones at
   sentence boundaries with linearly-interpolated timestamps. Approximate
   timestamps are fine for our use; we don't currently need word-level audio
   alignment.
"""

from __future__ import annotations

import re

from .transcribe import CallTranscript, Utterance

_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def clean_transcript(
    call: CallTranscript,
    *,
    microburst_max_words: int = 3,
    long_utterance_max_words: int = 120,
) -> CallTranscript:
    utterances = _merge_microbursts(call.utterances, max_words=microburst_max_words)
    utterances = _split_long_utterances(utterances, max_words=long_utterance_max_words)
    utterances = _reindex(utterances)
    return CallTranscript(
        audio_id=call.audio_id,
        duration_ms=call.duration_ms,
        utterances=utterances,
    )


def _merge_microbursts(utterances: list[Utterance], *, max_words: int) -> list[Utterance]:
    if len(utterances) < 3:
        return list(utterances)

    out: list[Utterance] = []
    i = 0
    while i < len(utterances):
        u = utterances[i]
        is_microburst = (
            out
            and i + 1 < len(utterances)
            and len(u.text.split()) <= max_words
            and out[-1].speaker == utterances[i + 1].speaker
            and u.speaker != out[-1].speaker
        )
        if is_microburst:
            prev = out[-1]
            nxt = utterances[i + 1]
            out[-1] = Utterance(
                idx=prev.idx,
                speaker=prev.speaker,
                text=f"{prev.text} {u.text} {nxt.text}",
                start_ms=prev.start_ms,
                end_ms=nxt.end_ms,
            )
            i += 2
            continue
        out.append(u)
        i += 1
    return out


def _split_long_utterances(utterances: list[Utterance], *, max_words: int) -> list[Utterance]:
    out: list[Utterance] = []
    for u in utterances:
        total_words = len(u.text.split())
        if total_words <= max_words:
            out.append(u)
            continue

        chunks = _chunk_by_sentences(u.text, max_words=max_words)
        if len(chunks) <= 1:
            out.append(u)
            continue

        duration = max(u.end_ms - u.start_ms, 1)
        cumulative_words = 0
        for chunk in chunks:
            chunk_words = len(chunk.split())
            chunk_start = u.start_ms + int(duration * cumulative_words / total_words)
            chunk_end = u.start_ms + int(
                duration * (cumulative_words + chunk_words) / total_words
            )
            out.append(
                Utterance(
                    idx=0,
                    speaker=u.speaker,
                    text=chunk,
                    start_ms=chunk_start,
                    end_ms=chunk_end,
                )
            )
            cumulative_words += chunk_words
    return out


def _chunk_by_sentences(text: str, *, max_words: int) -> list[str]:
    sentences = _SENT_SPLIT_RE.split(text.strip())
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0
    for sent in sentences:
        sent_words = len(sent.split())
        # If a single sentence exceeds the budget, emit it on its own.
        if sent_words > max_words and not current:
            chunks.append(sent)
            continue
        if current_words + sent_words > max_words and current:
            chunks.append(" ".join(current))
            current = [sent]
            current_words = sent_words
        else:
            current.append(sent)
            current_words += sent_words
    if current:
        chunks.append(" ".join(current))
    return chunks


def _reindex(utterances: list[Utterance]) -> list[Utterance]:
    return [
        Utterance(
            idx=i,
            speaker=u.speaker,
            text=u.text,
            start_ms=u.start_ms,
            end_ms=u.end_ms,
        )
        for i, u in enumerate(utterances)
    ]
