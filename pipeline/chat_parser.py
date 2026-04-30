"""Parse Zoom chat.txt into a roster of attendee display names.

Used to constrain the speaker-name resolution step: AssemblyAI returns
anonymous speaker IDs (A, B, C...), and we resolve them to real names
by looking at how Scott introduces clients during the call. The chat
roster gives us a closed candidate set to match against.

Chat lines look like:
    11:01:28<TAB>From <Sender> : <message>
    11:01:28<TAB>From <Sender>  To  Scott P. Scheper(privately) : <message>
    Replying to "..." / Reacted to "..." → continuation lines
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Lines that start a new message look like:  HH:MM:SS<TAB>From <name>[ To <recipient>(privately)] : <text>
_LINE_RE = re.compile(
    r"^\d{1,2}:\d{2}:\d{2}\s+From\s+(?P<sender>.+?)\s*(?:To\s+.+?\(privately\))?\s*:\s*(?P<text>.*)$"
)

# Bot/system senders we ignore when building the roster.
_BOT_SENDERS = {
    "read.ai meeting notes",
}


@dataclass(frozen=True)
class ChatMessage:
    sender: str
    text: str
    private_to_scott: bool
    is_reaction_or_reply: bool


def parse_chat(path: Path | str) -> list[ChatMessage]:
    path = Path(path)
    raw = path.read_text(encoding="utf-8", errors="replace")
    messages: list[ChatMessage] = []
    for line in raw.splitlines():
        m = _LINE_RE.match(line)
        if not m:
            continue
        sender = m.group("sender").strip()
        text = m.group("text").strip()
        if sender.lower() in _BOT_SENDERS:
            continue
        is_low_signal = text.startswith("Reacted to ") or text.startswith("Replying to ")
        private = "(privately)" in line
        messages.append(
            ChatMessage(
                sender=sender,
                text=text,
                private_to_scott=private,
                is_reaction_or_reply=is_low_signal,
            )
        )
    return messages


def attendee_roster(messages: list[ChatMessage]) -> list[str]:
    """Unique sender names in first-seen order. Includes anyone who posted at all."""
    seen: dict[str, None] = {}
    for msg in messages:
        if msg.sender not in seen:
            seen[msg.sender] = None
    return list(seen.keys())


def substantive_messages(messages: list[ChatMessage]) -> list[ChatMessage]:
    """Messages with real content — excludes pure reactions and reply markers."""
    return [m for m in messages if not m.is_reaction_or_reply]
