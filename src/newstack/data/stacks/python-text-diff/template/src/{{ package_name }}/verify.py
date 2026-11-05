"""Prove that applying a diff reproduces the other text, and say what broke if not."""

from __future__ import annotations

from dataclasses import dataclass

from .apply import apply_text
from .diff import diff_text, format_patch
from .model import CONTEXT, split_lines


@dataclass(frozen=True)
class Check:
    """One claim about a round trip, and whether it held."""

    name: str
    ok: bool
    detail: str

    def line(self) -> str:
        mark = "ok  " if self.ok else "FAIL"
        return f"{mark} {self.name:<28} {self.detail}"

    def as_dict(self) -> dict[str, object]:
        return {"name": self.name, "ok": self.ok, "detail": self.detail}


@dataclass(frozen=True)
class Verdict:
    """Every check for one pair of texts."""

    checks: tuple[Check, ...]

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks)

    def lines(self) -> list[str]:
        return [check.line() for check in self.checks]

    def as_dict(self) -> dict[str, object]:
        return {"ok": self.ok, "checks": [check.as_dict() for check in self.checks]}


def roundtrip(old: str, new: str, context: int = CONTEXT) -> Verdict:
    """Diff, apply, and diff again: the three claims that make a diff trustworthy."""
    checks: list[Check] = []
    patch = diff_text(old, new, context)
    if not patch.hunks:
        applied = apply_text(old, patch)
        checks.append(Check("the patch parses", applied.text == old, "no hunks to parse"))
        checks.append(Check("apply reproduces the new text", applied.text == new,
                            "identical" if applied.text == new else _where(applied.text, new)))
        checks.append(Check("diffing the result is empty", True, "there was nothing to change"))
        return Verdict(tuple(checks))
    checks.append(Check("the patch parses", _parses(format_patch(patch)),
                        f"{len(patch.hunks)} hunk(s)"))
    applied = apply_text(old, patch)
    checks.append(Check("apply reproduces the new text", applied.text == new,
                        "identical" if applied.text == new else _where(applied.text, new)))
    again = diff_text(applied.text, new, context)
    checks.append(Check("diffing the result is empty", not again.hunks,
                        "no hunks" if not again.hunks else f"{len(again.hunks)} hunk(s) left"))
    return Verdict(tuple(checks))


def _parses(text: str) -> bool:
    from .diff import parse_patch

    try:
        parse_patch(text)
    except Exception:
        return False
    return True


def _where(got: str, want: str) -> str:
    left, right = split_lines(got), split_lines(want)
    for index in range(max(len(left), len(right))):
        here = left[index] if index < len(left) else None
        there = right[index] if index < len(right) else None
        if here != there:
            return f"line {index + 1}: {here!r} != {there!r}"
    return "identical line lists"
