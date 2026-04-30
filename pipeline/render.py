from .models import ClientResponseDoc

SEPARATOR = "---"


def render(doc: ClientResponseDoc) -> str:
    sections = [
        _metadata(doc),
        _section("Client Question", doc.client_question.strip()),
        _bullet_section("Distilled Advice", doc.distilled_advice),
        _bullet_section("Key Principles", doc.key_principles),
        _transcript(doc),
    ]
    return "\n\n".join(sections).rstrip() + "\n"


def _metadata(doc: ClientResponseDoc) -> str:
    topics = ", ".join(doc.topics)
    body = "\n".join(
        [
            f"DATE: {doc.call_date.isoformat()}",
            f"CLIENT: {doc.client_first_name} {doc.client_last_name}",
            f"PROGRAM: {doc.program}",
            f"TOPICS: {topics}",
            f"CONTENT_TYPE: {doc.content_type}",
        ]
    )
    return f"## Metadata\n\n{body}\n\n{SEPARATOR}"


def _section(title: str, body: str) -> str:
    return f"## {title}\n\n{body}\n\n{SEPARATOR}"


def _bullet_section(title: str, items: list[str]) -> str:
    bullets = "\n".join(f"- {item.strip()}" for item in items)
    return f"## {title}\n\n{bullets}\n\n{SEPARATOR}"


def _transcript(doc: ClientResponseDoc) -> str:
    blocks: list[str] = []
    for turn in doc.transcript:
        text = turn.text.strip()
        if not text:
            continue
        blocks.append(f"{turn.speaker}: {text}")
    body = "\n\n".join(blocks)
    return f"## Transcript\n\n{body}"
