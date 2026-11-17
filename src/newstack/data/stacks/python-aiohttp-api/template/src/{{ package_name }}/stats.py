"""Small text-analysis helpers shared by the HTTP handlers."""

from __future__ import annotations


def analyze(text: str) -> dict[str, object]:
    data = text.encode()
    lines = data.count(b"\n")
    if data and not data.endswith(b"\n"):
        lines += 1
    words = len(text.split())
    return {
        "text": text,
        "lines": lines,
        "words": words,
        "bytes": len(data),
    }