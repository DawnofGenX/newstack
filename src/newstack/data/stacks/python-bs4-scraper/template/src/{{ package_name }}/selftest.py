"""Offline self-test."""

from __future__ import annotations

from pathlib import Path

from .extract import extract_cards, extract_tables


def _sample_html() -> str:
    local = Path("fixtures/sample.html")
    if local.exists():
        return local.read_text(encoding="utf-8")
    root = Path(__file__).resolve().parents[2]
    return (root / "fixtures" / "sample.html").read_text(encoding="utf-8")


def run() -> int:
    html = _sample_html()
    tables = extract_tables(html)
    assert sum(len(t) for t in tables) == 3, tables
    cards = extract_cards(html)
    assert len(cards) == 2, cards
    print("selftest: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
