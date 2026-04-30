"""Render a hand-built ClientResponseDoc to verify the markdown shape.

Output is printed to stdout; eyeball it against examples/Examples/*.md.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.models import ClientResponseDoc, TranscriptTurn  # noqa: E402
from pipeline.render import render  # noqa: E402


def main() -> int:
    doc = ClientResponseDoc(
        call_date=date(2025, 2, 26),
        client_first_name="Tracy",
        client_last_name="Hawkings",
        client_display_name="Tracy Hawkings",
        topics=[
            "book writing",
            "developmental editing",
            "resistance",
            "publishing",
            "positioning",
            "messaging",
        ],
        client_question=(
            "Tracy submitted a nearly complete book (95% done) and asked for "
            "developmental editing feedback, including guidance on title, "
            "subtitle, and overall direction before publishing."
        ),
        distilled_advice=[
            "Choose a subtitle that is simple, clear, and broadly appealing",
            "Sell the desired outcome on the cover, deliver the real work inside the book",
            "Ship the book even if it feels imperfect",
        ],
        key_principles=[
            '"Sell what people want, give them what they need"',
            "Perfectionism is often disguised procrastination",
            "Shipping is more important than refining beyond a certain point",
        ],
        transcript=[
            TranscriptTurn(
                speaker="Scott P. Scheper",
                text=(
                    "Okay. Awesome. Okay, next. We've got Tracy Hawkings. Tracy, go ahead "
                    "and do a digital hand raise."
                ),
            ),
            TranscriptTurn(
                speaker="Scott P. Scheper",
                text=(
                    "For Tracy, this is the one that resonated with me most: A Homecoming "
                    "Journey for Women 50+. It's simple, straightforward, and I like it "
                    "better than the alternatives."
                ),
            ),
        ],
    )

    out = render(doc)
    print(out)
    print("---")
    print(f"slug:     {doc.slug()}")
    print(f"filename: {doc.filename()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
