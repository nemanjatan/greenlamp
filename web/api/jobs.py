"""In-memory job store + background pipeline runner.

A job is created when the frontend submits an Uploadcare URL; a worker thread
runs the pipeline against that URL and uploads each generated MD plus a
combined ZIP back to Uploadcare. The job dict is read by the polling endpoint.
"""

from __future__ import annotations

import io
import threading
import time
import traceback
import uuid
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from pipeline.cleanup import clean_transcript
from pipeline.enrich import enrich_segment
from pipeline.models import ClientResponseDoc, TranscriptTurn
from pipeline.polish import polish
from pipeline.render import render
from pipeline.segment import analyze_call
from pipeline.transcribe import transcribe

from .schemas import JobDTO, JobResultDTO, JobStage
from .uploadcare import upload_bytes


@dataclass
class JobResult:
    client_first_name: str
    client_last_name: str
    client_display_name: str
    filename: str
    markdown: str
    cdn_url: str
    topics: list[str]


@dataclass
class Job:
    id: str
    audio_filename: str
    stage: JobStage = JobStage.queued
    progress_pct: int = 0
    duration_ms: int = 0
    utterance_count: int = 0
    segments_count: int = 0
    results: list[JobResult] = field(default_factory=list)
    zip_url: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    finished_at: Optional[float] = None

    def to_dto(self) -> JobDTO:
        return JobDTO(
            id=self.id,
            stage=self.stage,
            progress_pct=self.progress_pct,
            audio_filename=self.audio_filename,
            duration_ms=self.duration_ms,
            utterance_count=self.utterance_count,
            segments_count=self.segments_count,
            results=[
                JobResultDTO(
                    client_first_name=r.client_first_name,
                    client_last_name=r.client_last_name,
                    client_display_name=r.client_display_name,
                    filename=r.filename,
                    markdown=r.markdown,
                    cdn_url=r.cdn_url,
                    topics=r.topics,
                )
                for r in self.results
            ],
            zip_url=self.zip_url,
            error=self.error,
            started_at=self.started_at,
            finished_at=self.finished_at,
        )


_JOBS: dict[str, Job] = {}
_LOCK = threading.Lock()


def create_job(audio_filename: str) -> Job:
    job = Job(id=str(uuid.uuid4()), audio_filename=audio_filename)
    with _LOCK:
        _JOBS[job.id] = job
    return job


def get_job(job_id: str) -> Optional[Job]:
    with _LOCK:
        return _JOBS.get(job_id)


def start_job(job_id: str, audio_url: str) -> None:
    threading.Thread(target=_run, args=(job_id, audio_url), daemon=True).start()


def _run(job_id: str, audio_url: str) -> None:
    job = get_job(job_id)
    if job is None:
        return
    job.started_at = time.time()
    try:
        # 1. transcribe (longest stage — typically 30-50% of audio duration)
        job.stage = JobStage.transcribing
        job.progress_pct = 5
        call = transcribe(audio_url, cache_path=None)
        job.duration_ms = call.duration_ms
        job.utterance_count = len(call.utterances)
        job.progress_pct = 55

        # 2. cleanup
        job.stage = JobStage.cleaning
        call = clean_transcript(call)
        job.utterance_count = len(call.utterances)
        job.progress_pct = 60

        # 3. segment
        job.stage = JobStage.segmenting
        analysis = analyze_call(call, chat_roster=[])
        job.segments_count = len(analysis.segments)
        job.progress_pct = 70
        speaker_to_name = {s.speaker_label: s.name for s in analysis.speakers}

        # 4. group segments by client + enrich + render
        job.stage = JobStage.enriching
        grouped = _group_segments_by_client(analysis.segments)
        call_date = date.today()
        markdown_files: list[tuple[str, bytes]] = []
        n = max(len(grouped), 1)

        for i, (_, segs) in enumerate(grouped.items()):
            utts = []
            for seg in segs:
                utts.extend(call.utterances[seg.start_utterance_idx:seg.end_utterance_idx])
            if not utts:
                continue

            seg_text = "\n".join(
                f"{speaker_to_name.get(u.speaker, u.speaker)}: {u.text}" for u in utts
            )
            e = enrich_segment(seg_text)

            turns: list[TranscriptTurn] = []
            for u in utts:
                label = speaker_to_name.get(u.speaker, u.speaker)
                if turns and turns[-1].speaker == label:
                    turns[-1].text = f"{turns[-1].text} {u.text}"
                else:
                    turns.append(TranscriptTurn(speaker=label, text=u.text))
            for t in turns:
                t.text = polish(t.text)

            rep = segs[0]
            doc = ClientResponseDoc(
                call_date=call_date,
                client_first_name=rep.client_first_name,
                client_last_name=rep.client_last_name,
                client_display_name=rep.client_display_name,
                topics=e.topics,
                client_question=e.client_question,
                distilled_advice=e.distilled_advice,
                key_principles=e.key_principles,
                transcript=turns,
            )
            md_text = render(doc)
            markdown_files.append((doc.filename(), md_text.encode("utf-8")))

            cdn_url = upload_bytes(md_text.encode("utf-8"), doc.filename())
            job.results.append(
                JobResult(
                    client_first_name=doc.client_first_name,
                    client_last_name=doc.client_last_name,
                    client_display_name=doc.client_display_name,
                    filename=doc.filename(),
                    markdown=md_text,
                    cdn_url=cdn_url,
                    topics=doc.topics,
                )
            )
            job.progress_pct = 70 + int(20 * (i + 1) / n)

        # 5. bundle zip and upload
        job.stage = JobStage.uploading
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname, content in markdown_files:
                zf.writestr(fname, content)
        zip_filename = f"wtf_{call_date.isoformat()}_responses.zip"
        job.zip_url = upload_bytes(zip_buffer.getvalue(), zip_filename)

        job.stage = JobStage.complete
        job.progress_pct = 100
    except Exception as exc:
        traceback.print_exc()
        job.stage = JobStage.failed
        job.error = f"{type(exc).__name__}: {exc}"
    finally:
        job.finished_at = time.time()


def _group_segments_by_client(segments):
    grouped: dict[tuple[str, str], list] = defaultdict(list)
    for seg in segments:
        key = (seg.client_first_name.strip().lower(), seg.client_last_name.strip().lower())
        grouped[key].append(seg)
    for key in grouped:
        grouped[key].sort(key=lambda s: s.start_utterance_idx)
    seen: dict = {}
    for seg in segments:
        key = (seg.client_first_name.strip().lower(), seg.client_last_name.strip().lower())
        if key not in seen:
            seen[key] = grouped[key]
    return seen
