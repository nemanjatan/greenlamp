"""Light filler removal applied to per-turn transcript text before render.

Per Scott's confirmation in Upwork (2026-04-30): drop "uh" / "um" / "ah"
stutters and collapse adjacent word repetitions ("the, the" -> "the").
Preserves Scott's words otherwise — does not remove "you know" / "like" /
"I mean" since those can carry meaning.
"""

from __future__ import annotations

import re

# Standalone "uh" / "um" / "ah" with any trailing comma+space.
_FILLER_RE = re.compile(r"\b(uh|um|ah)\b\s*,?\s*", re.IGNORECASE)

# Cleanup of resulting punctuation glitches.
_DOTCOMMA_RE = re.compile(r",\s*\.")
_DOUBLE_COMMA_RE = re.compile(r",\s*,")
_MULTI_SPACE_RE = re.compile(r"\s+")
_SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([.,!?;:])")


def polish(text: str) -> str:
    text = _remove_fillers(text)
    # Word-level collapse first so "the, the, the" doesn't sit between two
    # otherwise-detectable "the main, the main" phrases.
    text = _collapse_word_repeats(text)
    text = _collapse_phrase_repeats(text, n=3)
    text = _collapse_phrase_repeats(text, n=2)
    return text


def _collapse_phrase_repeats(text: str, n: int) -> str:
    """Collapse repeated n-token phrases: 'the main, the main' -> 'the main'.

    Keeps the second occurrence's punctuation (typically clean) rather than the
    first's (which often has the trailing-comma separator that joined the pair).
    """
    tokens = text.split()
    if len(tokens) < 2 * n:
        return text

    def bare(tok: str) -> str:
        return tok.rstrip(",.;:?!").lower()

    result: list[str] = []
    i = 0
    while i < len(tokens):
        if i + 2 * n <= len(tokens):
            phrase1 = [bare(t) for t in tokens[i:i + n]]
            phrase2 = [bare(t) for t in tokens[i + n:i + 2 * n]]
            if all(phrase1) and phrase1 == phrase2:
                result.extend(tokens[i + n:i + 2 * n])
                i += 2 * n
                continue
        result.append(tokens[i])
        i += 1
    return " ".join(result)


def _remove_fillers(text: str) -> str:
    text = _FILLER_RE.sub("", text)
    text = _DOTCOMMA_RE.sub(".", text)
    text = _DOUBLE_COMMA_RE.sub(",", text)
    text = _MULTI_SPACE_RE.sub(" ", text)
    text = _SPACE_BEFORE_PUNCT_RE.sub(r"\1", text)
    return text.strip()


def _collapse_word_repeats(text: str) -> str:
    """Collapse identical adjacent words: 'I, I think' -> 'I think', 'the the' -> 'the'.

    Preserves the second occurrence's punctuation, so trailing commas/periods
    that were attached to the duplicate stay attached after the collapse.
    """
    tokens = text.split()
    result: list[str] = []
    for token in tokens:
        bare = token.rstrip(",.;:?!").lower()
        if result and bare and bare == result[-1].rstrip(",.;:?!").lower():
            result[-1] = token
            continue
        result.append(token)
    return " ".join(result)
