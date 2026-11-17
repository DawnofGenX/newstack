"""{{ title }} package."""

from __future__ import annotations

REVISIONS = ("0001", "0002")


def latest_revision() -> str:
    return REVISIONS[-1]