"""Check the OUTPUT, never the input: a sanitizer is judged by what it emits."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .policy import DEFAULT, Policy
from .sanitize import Stats, explain

TAG = re.compile(r"<[^>]*>")

#: Constructs that must not appear inside any tag of the output.
DANGER: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("script tag", re.compile(r"<\s*script", re.I)),
    ("iframe tag", re.compile(r"<\s*iframe", re.I)),
    ("plugin tag", re.compile(r"<\s*(?:object|embed|applet)", re.I)),
    ("style tag", re.compile(r"<\s*style", re.I)),
    ("javascript url", re.compile(r"javascript\s*:", re.I)),
    ("vbscript url", re.compile(r"vbscript\s*:", re.I)),
    ("inline html data url", re.compile(r"data\s*:\s*text/html", re.I)),
    ("inline event handler", re.compile(r"\son[a-z]+\s*=", re.I)),
)


def problems(output: str) -> list[str]:
    """Dangerous constructs in the tags of `output`, with where they were found."""
    found: list[str] = []
    for match in TAG.finditer(output):
        tag = match.group(0)
        for label, pattern in DANGER:
            if pattern.search(tag):
                found.append(f"{label} in {tag[:60]!r}")
    return found


@dataclass(frozen=True)
class Verdict:
    """What a sanitizer must satisfy: nothing dangerous, and stable under itself."""

    source: str
    output: str
    idempotent: bool
    problems: tuple[str, ...]
    stats: Stats

    @property
    def ok(self) -> bool:
        return self.idempotent and not self.problems

    def line(self) -> str:
        if self.ok:
            return "ok       nothing dangerous survives, and the output is a fixed point"
        reasons = []
        if self.problems:
            reasons.append(f"{len(self.problems)} dangerous construct(s)")
        if not self.idempotent:
            reasons.append("a second pass changes the output")
        return "FAIL     " + "; ".join(reasons)

    def as_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "output": self.output,
            "idempotent": self.idempotent,
            "problems": list(self.problems),
            "stats": self.stats.as_dict(),
        }


def audit(text: str, policy: Policy = DEFAULT) -> Verdict:
    once, stats = explain(text, policy)
    twice, _ = explain(once, policy)
    return Verdict(
        source=text,
        output=once,
        idempotent=once == twice,
        problems=tuple(problems(once)),
        stats=stats,
    )
