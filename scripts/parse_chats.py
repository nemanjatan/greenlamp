"""Parse all Zoom chat.txt files into per-call attendee rosters.

Writes one JSON per call into data/rosters/ and prints a summary table.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Make `pipeline` importable when running this script directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.chat_parser import attendee_roster, parse_chat, substantive_messages  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = ROOT / "examples"
ROSTERS_DIR = ROOT / "data" / "rosters"

# Folder names look like "2025-02-26 11.00.21 Write to Freedom Weekly Call".
_CALL_DIR_RE = re.compile(r"^(?P<date>\d{4}-\d{2}-\d{2})\s")


def main() -> int:
    ROSTERS_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[tuple[str, int, int, int, int]] = []  # date, total, substantive, private, unique

    for folder in sorted(EXAMPLES_DIR.iterdir()):
        if not folder.is_dir():
            continue
        m = _CALL_DIR_RE.match(folder.name)
        if not m:
            continue
        chat_path = folder / "chat.txt"
        if not chat_path.exists():
            continue

        date_str = m.group("date")
        messages = parse_chat(chat_path)
        roster = attendee_roster(messages)
        substantive = substantive_messages(messages)
        private_msgs = sum(1 for msg in messages if msg.private_to_scott)

        out_path = ROSTERS_DIR / f"{date_str}.json"
        out_path.write_text(
            json.dumps(
                {
                    "call_date": date_str,
                    "folder": folder.name,
                    "attendee_count": len(roster),
                    "attendees": roster,
                    "message_counts": {
                        "total": len(messages),
                        "substantive": len(substantive),
                        "private_to_scott": private_msgs,
                    },
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        rows.append((date_str, len(messages), len(substantive), private_msgs, len(roster)))

    if not rows:
        print("No chat.txt files found under examples/.", file=sys.stderr)
        return 1

    print(f"{'CALL DATE':12}  {'TOTAL':>5}  {'SUBST':>5}  {'PRIVATE':>7}  {'UNIQUE':>6}")
    print("-" * 50)
    for date_str, total, substantive, private, unique in rows:
        print(f"{date_str:12}  {total:>5}  {substantive:>5}  {private:>7}  {unique:>6}")
    print(f"\nWrote rosters to {ROSTERS_DIR.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
