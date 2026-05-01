"""Validate every Markdown file in data/output/ against the test-spec format.

Checks performed per file:
  1. Filename pattern: wtf_zoom-response_YYYY-MM-DD_<slug>.md
  2. Metadata block has all 5 required fields with non-empty values:
     DATE (YYYY-MM-DD), CLIENT, PROGRAM ("Write to Freedom"),
     TOPICS (comma-separated, non-empty),
     CONTENT_TYPE ("Zoom Response" | "Email Response" | "Loom Response").
  3. The four required H2 sections are present, in order:
     ## Metadata, ## Client Question, ## Distilled Advice,
     ## Key Principles, ## Transcript.
  4. Distilled Advice and Key Principles are bullet lists with >= 3 items.
  5. Transcript contains at least one "Speaker: text" turn.
  6. No standalone "uh" / "um" / "ah" / "er" filler appears anywhere
     (Scott's Q2 answer: drop the 'uh' stutters).

Exits 0 if all files pass, 1 otherwise.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "data" / "output"

FILENAME_RE = re.compile(r"^wtf_zoom-response_\d{4}-\d{2}-\d{2}_[a-z0-9-]+\.md$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SECTION_RE = re.compile(r"^## (.+)$", re.MULTILINE)
META_LINE_RE = re.compile(r"^([A-Z_]+):\s*(.*)$")
SPEAKER_LINE_RE = re.compile(r"^[A-Za-z][A-Za-z. ,'\-]+:\s+\S")
FILLER_RE = re.compile(r"\b(uh|um|ah|er)\b", re.IGNORECASE)
ALLOWED_CONTENT_TYPES = {"Zoom Response", "Email Response", "Loom Response"}
REQUIRED_META = ["DATE", "CLIENT", "PROGRAM", "TOPICS", "CONTENT_TYPE"]
REQUIRED_SECTIONS = [
    "Metadata",
    "Client Question",
    "Distilled Advice",
    "Key Principles",
    "Transcript",
]


@dataclass
class Report:
    path: Path
    issues: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues


def main() -> int:
    if not OUTPUT_DIR.exists():
        print(f"data/output/ not found at {OUTPUT_DIR}", file=sys.stderr)
        return 1

    md_files = sorted(OUTPUT_DIR.glob("*.md"))
    if not md_files:
        print(f"No .md files in {OUTPUT_DIR}", file=sys.stderr)
        return 1

    reports = [check_file(p) for p in md_files]
    failed = [r for r in reports if not r.ok]

    for r in reports:
        marker = "OK " if r.ok else "FAIL"
        print(f"  [{marker}] {r.path.name}")
        for issue in r.issues:
            print(f"         - {issue}")

    print()
    print("-" * 60)
    print(f"  {len(reports) - len(failed)}/{len(reports)} files passed")
    if failed:
        print(f"  {len(failed)} file(s) failed validation:")
        for r in failed:
            print(f"    - {r.path.name}")
    return 0 if not failed else 1


def check_file(path: Path) -> Report:
    report = Report(path=path)
    text = path.read_text(encoding="utf-8")

    _check_filename(path, report)
    _check_sections_present(text, report)
    _check_metadata(text, report)
    _check_bullet_section(text, "Distilled Advice", min_items=3, report=report)
    _check_bullet_section(text, "Key Principles", min_items=3, report=report)
    _check_transcript(text, report)
    _check_no_filler(text, report)
    return report


def _check_filename(path: Path, report: Report) -> None:
    if not FILENAME_RE.match(path.name):
        report.issues.append(
            f"filename does not match wtf_zoom-response_YYYY-MM-DD_<slug>.md: {path.name!r}"
        )


def _check_sections_present(text: str, report: Report) -> None:
    found = SECTION_RE.findall(text)
    for required in REQUIRED_SECTIONS:
        if required not in found:
            report.issues.append(f"missing required section: '## {required}'")
    # Check order — strip out unknown sections, ensure remaining sequence is in order.
    relevant = [s for s in found if s in REQUIRED_SECTIONS]
    if relevant != [s for s in REQUIRED_SECTIONS if s in relevant]:
        report.issues.append(
            f"sections not in expected order: got {relevant!r}, expected {REQUIRED_SECTIONS!r}"
        )


def _section_body(text: str, name: str) -> str | None:
    """Return the body of `## name` up to the next ## or end of file."""
    match = re.search(rf"^## {re.escape(name)}\s*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else None


def _check_metadata(text: str, report: Report) -> None:
    body = _section_body(text, "Metadata")
    if body is None:
        return  # already reported as missing
    fields: dict[str, str] = {}
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("---"):
            continue
        m = META_LINE_RE.match(line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    for key in REQUIRED_META:
        if key not in fields:
            report.issues.append(f"metadata missing key: {key}")
        elif not fields[key]:
            report.issues.append(f"metadata key {key} is empty")
    if "DATE" in fields and fields["DATE"] and not DATE_RE.match(fields["DATE"]):
        report.issues.append(f"DATE is not YYYY-MM-DD: {fields['DATE']!r}")
    if fields.get("PROGRAM") and fields["PROGRAM"] != "Write to Freedom":
        report.issues.append(f"PROGRAM should be 'Write to Freedom', got {fields['PROGRAM']!r}")
    if fields.get("CONTENT_TYPE") and fields["CONTENT_TYPE"] not in ALLOWED_CONTENT_TYPES:
        report.issues.append(
            f"CONTENT_TYPE should be one of {sorted(ALLOWED_CONTENT_TYPES)}, "
            f"got {fields['CONTENT_TYPE']!r}"
        )
    topics = fields.get("TOPICS", "")
    if topics and len([t for t in topics.split(",") if t.strip()]) < 2:
        report.issues.append(f"TOPICS has fewer than 2 entries: {topics!r}")


def _check_bullet_section(text: str, name: str, *, min_items: int, report: Report) -> None:
    body = _section_body(text, name)
    if body is None:
        return  # missing-section already reported
    bullets = [line for line in body.splitlines() if re.match(r"^\s*-\s+\S", line)]
    if len(bullets) < min_items:
        report.issues.append(
            f"{name!r} has {len(bullets)} bullet item(s); expected at least {min_items}"
        )


def _check_transcript(text: str, report: Report) -> None:
    body = _section_body(text, "Transcript")
    if body is None:
        return
    speaker_lines = [line for line in body.splitlines() if SPEAKER_LINE_RE.match(line)]
    if not speaker_lines:
        report.issues.append("transcript has no recognisable 'Speaker: text' lines")


def _check_no_filler(text: str, report: Report) -> None:
    matches = FILLER_RE.findall(text)
    if matches:
        # show counts grouped by token
        counts: dict[str, int] = {}
        for m in matches:
            key = m.lower()
            counts[key] = counts.get(key, 0) + 1
        summary = ", ".join(f"{k}×{v}" for k, v in sorted(counts.items()))
        report.issues.append(f"filler tokens still present: {summary}")


if __name__ == "__main__":
    raise SystemExit(main())
