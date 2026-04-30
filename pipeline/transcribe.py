"""AssemblyAI transcription with on-disk caching.

The cache is keyed by the destination JSON path (typically
`data/transcripts/<call-date>.json`). Re-running the pipeline is free
unless `force=True` is passed.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

import assemblyai as aai


@dataclass(frozen=True)
class Utterance:
    idx: int
    speaker: str  # AssemblyAI speaker tag: "A", "B", "C", ...
    text: str
    start_ms: int
    end_ms: int


@dataclass(frozen=True)
class CallTranscript:
    audio_id: str
    duration_ms: int
    utterances: list[Utterance]

    def as_indexed_text(self) -> str:
        """Format utterances for LLM consumption: '[idx] SPEAKER: text' per line."""
        return "\n".join(
            f"[{u.idx}] {u.speaker}: {u.text}" for u in self.utterances
        )


def transcribe(
    audio_path: Path | str,
    cache_path: Path | str,
    *,
    api_key: str | None = None,
    force: bool = False,
    speech_model: str = "universal",
) -> CallTranscript:
    audio_path = Path(audio_path)
    cache_path = Path(cache_path)

    if cache_path.exists() and not force:
        return _load_cache(cache_path)

    key = api_key or os.environ.get("ASSEMBLYAI_API_KEY")
    if not key:
        raise RuntimeError(
            "ASSEMBLYAI_API_KEY is not set. Add it to .env or pass api_key explicitly."
        )
    aai.settings.api_key = key

    config = aai.TranscriptionConfig(
        speaker_labels=True,
        speech_models=[_resolve_speech_model(speech_model).value],
    )
    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe(str(audio_path))

    if transcript.status != aai.TranscriptStatus.completed:
        raise RuntimeError(
            f"AssemblyAI transcription failed (status={transcript.status}): {transcript.error}"
        )

    utterances: list[Utterance] = []
    for i, u in enumerate(transcript.utterances or []):
        utterances.append(
            Utterance(
                idx=i,
                speaker=u.speaker,
                text=u.text,
                start_ms=int(u.start),
                end_ms=int(u.end),
            )
        )

    result = CallTranscript(
        audio_id=transcript.id,
        duration_ms=int((transcript.audio_duration or 0) * 1000),
        utterances=utterances,
    )

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(_serialize(result), encoding="utf-8")
    return result


def _resolve_speech_model(name: str) -> aai.SpeechModel:
    normalized = name.lower().replace("_", "-")
    try:
        return aai.SpeechModel(normalized)
    except ValueError as e:
        valid = [m.value for m in aai.SpeechModel]
        raise ValueError(f"Unknown speech model {name!r}. Valid: {valid}") from e


def _serialize(t: CallTranscript) -> str:
    return json.dumps(
        {
            "audio_id": t.audio_id,
            "duration_ms": t.duration_ms,
            "utterances": [
                {
                    "idx": u.idx,
                    "speaker": u.speaker,
                    "text": u.text,
                    "start_ms": u.start_ms,
                    "end_ms": u.end_ms,
                }
                for u in t.utterances
            ],
        },
        indent=2,
        ensure_ascii=False,
    )


def _load_cache(path: Path) -> CallTranscript:
    raw = json.loads(path.read_text(encoding="utf-8"))
    utterances = [
        Utterance(
            idx=u["idx"],
            speaker=u["speaker"],
            text=u["text"],
            start_ms=u["start_ms"],
            end_ms=u["end_ms"],
        )
        for u in raw["utterances"]
    ]
    return CallTranscript(
        audio_id=raw["audio_id"],
        duration_ms=raw["duration_ms"],
        utterances=utterances,
    )
