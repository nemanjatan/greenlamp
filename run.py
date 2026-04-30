"""Process a single Zoom call folder into per-client Markdown files.

Usage:
    python run.py "examples/2025-04-16 11.00.43 Write to Freedom Weekly Call"
    python run.py <folder> --force                # bypass transcript cache
    python run.py <folder> --speech-model slam_1  # override AssemblyAI model
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from pipeline.enrich import enrich_segment
from pipeline.models import ClientResponseDoc, TranscriptTurn
from pipeline.render import render
from pipeline.segment import analyze_call
from pipeline.transcribe import CallTranscript, transcribe


_DATE_RE = re.compile(r"^(?P<date>\d{4}-\d{2}-\d{2})\s")
_ROOT = Path(__file__).resolve().parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("call_folder", type=Path)
    parser.add_argument("--force", action="store_true", help="Re-transcribe even if a cache file exists.")
    parser.add_argument("--speech-model", default="universal")
    parser.add_argument(
        "--openai-model",
        default="gpt-4.1",
        help="OpenAI model for both the segmentation and enrichment passes.",
    )
    args = parser.parse_args(argv)

    load_dotenv(_ROOT / ".env")

    folder = args.call_folder.resolve()
    m = _DATE_RE.match(folder.name)
    if not m:
        print(f"Folder name must start with YYYY-MM-DD: {folder.name}", file=sys.stderr)
        return 2
    call_date = date.fromisoformat(m.group("date"))

    audio = next(folder.glob("audio*.m4a"), None) or next(folder.glob("video*.mp4"), None)
    if audio is None:
        print(f"No audio*.m4a or video*.mp4 in {folder}", file=sys.stderr)
        return 2

    chat_roster = _load_chat_roster(call_date)
    cache_path = _ROOT / "data" / "transcripts" / f"{call_date.isoformat()}.json"

    print(f"[transcribe] {audio.name}  cached={cache_path.exists() and not args.force}")
    call = transcribe(audio, cache_path, force=args.force, speech_model=args.speech_model)
    print(f"             -> {len(call.utterances)} utterances, {call.duration_ms / 60_000:.1f} min")

    print(f"[segment]    resolving speakers and partitioning into client blocks...")
    analysis = analyze_call(call, chat_roster, model=args.openai_model)
    speaker_to_name = {s.speaker_label: s.name for s in analysis.speakers}
    print(f"             -> {len(analysis.speakers)} speakers, {len(analysis.segments)} client segment(s)")
    for s in analysis.speakers:
        print(f"                speaker {s.speaker_label} = {s.name} ({s.role})")

    output_dir = _ROOT / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for seg in analysis.segments:
        utts = call.utterances[seg.start_utterance_idx:seg.end_utterance_idx]
        if not utts:
            print(f"             ! empty segment for {seg.client_first_name} {seg.client_last_name}; skipping")
            continue

        seg_text = "\n".join(
            f"{speaker_to_name.get(u.speaker, u.speaker)}: {u.text}" for u in utts
        )

        print(f"[enrich]     {seg.client_first_name} {seg.client_last_name} (utt {seg.start_utterance_idx}..{seg.end_utterance_idx}, {len(utts)} utterances)")
        e = enrich_segment(seg_text, model=args.openai_model)

        turns = _group_consecutive_speakers(utts, speaker_to_name)
        doc = ClientResponseDoc(
            call_date=call_date,
            client_first_name=seg.client_first_name,
            client_last_name=seg.client_last_name,
            client_display_name=seg.client_display_name,
            topics=e.topics,
            client_question=e.client_question,
            distilled_advice=e.distilled_advice,
            key_principles=e.key_principles,
            transcript=turns,
        )

        out_path = output_dir / doc.filename()
        out_path.write_text(render(doc), encoding="utf-8")
        written.append(out_path)
        print(f"[render]     wrote {out_path.relative_to(_ROOT)}")

    print(f"\nDone. {len(written)} markdown file(s) in {(_ROOT / 'data' / 'output').relative_to(_ROOT)}/")
    return 0


def _load_chat_roster(call_date: date) -> list[str]:
    path = _ROOT / "data" / "rosters" / f"{call_date.isoformat()}.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("attendees", [])


def _group_consecutive_speakers(utts, speaker_to_name) -> list[TranscriptTurn]:
    turns: list[TranscriptTurn] = []
    for u in utts:
        label = speaker_to_name.get(u.speaker, u.speaker)
        if turns and turns[-1].speaker == label:
            turns[-1].text = f"{turns[-1].text} {u.text}"
        else:
            turns.append(TranscriptTurn(speaker=label, text=u.text))
    return turns


if __name__ == "__main__":
    raise SystemExit(main())
