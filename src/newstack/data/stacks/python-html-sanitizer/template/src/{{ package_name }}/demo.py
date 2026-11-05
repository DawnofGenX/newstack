"""Eight inputs that are ordinary in the wild, and what a rebuild produces."""

from __future__ import annotations

from dataclasses import dataclass

from .audit import audit
from .policy import DEFAULT, Policy
from .sanitize import explain

#: (name, source, what the output must show)
VECTORS: tuple[tuple[str, str, str], ...] = (
    (
        "a script block",
        "<p>hello</p><script>alert(1)</script><p>bye</p>",
        "the payload is gone, not escaped",
    ),
    (
        "an image with an event handler",
        '<img src=x onerror="alert(1)">',
        "the tag is dropped, and it has no text to keep",
    ),
    (
        "a javascript url",
        '<a href="javascript:alert(1)">click</a>',
        "the link survives, the url does not",
    ),
    (
        "a url that hides its scheme",
        '<a href="jav&#x09;ascript&#58;alert(1)">x</a>',
        "a tab inside the scheme changes nothing",
    ),
    (
        "attributes nobody allowed",
        '<p onclick="steal()" style="color:red">text</p>',
        "the element stays, its handlers do not",
    ),
    (
        "markup that does not nest",
        "<b><i>bold italic</b></i>",
        "the output is closed in the order it was opened",
    ),
    ("text that looks like markup", "5 < 6 & 7 > 2", "characters are escaped, not sanitized away"),
    ("a comment", "<p>visible</p><!-- secret -->", "comments are not content"),
)


@dataclass(frozen=True)
class Step:
    name: str
    lines: tuple[str, ...]
    ok: bool

    def render(self) -> str:
        verdict = "as advertised" if self.ok else "NOT AS ADVERTISED"
        body = "".join(f"  {line}\n" for line in self.lines)
        return f"{self.name:<32} {verdict}\n{body}"


def _step(name: str, source: str, note: str, policy: Policy) -> Step:
    verdict = audit(source, policy)
    lines = [
        f"in       {source}",
        f"out      {verdict.output!r}",
        f"{note}",
        verdict.line(),
    ]
    if not verdict.ok:
        lines.extend(f"problem  {problem}" for problem in verdict.problems)
        if not verdict.idempotent:
            lines.append("problem  the second pass produced different bytes")
    return Step(name=name, lines=tuple(lines), ok=verdict.ok)


def run(policy: Policy = DEFAULT) -> list[Step]:
    return [_step(name, source, note, policy) for name, source, note in VECTORS]


def render(steps: list[Step]) -> list[str]:
    lines: list[str] = []
    for step in steps:
        lines.append(step.render())
    missed = sum(1 for step in steps if not step.ok)
    lines.append(f"demo: {len(steps)} vectors, {missed} not as advertised")
    return lines


def stats_line(source: str, policy: Policy = DEFAULT) -> str:
    _output, stats = explain(source, policy)
    return stats.line()


def payload(steps: list[Step]) -> dict[str, object]:
    return {
        "vectors": len(steps),
        "missed": sum(1 for step in steps if not step.ok),
        "ok": all(step.ok for step in steps),
    }
