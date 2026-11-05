"""Seven claims about a diff, each one shown by running it rather than asserted."""

from __future__ import annotations

from dataclasses import dataclass

from .apply import Applied, apply_text
from .diff import diff_text, format_patch, parse_patch
from .model import DiffError
from .verify import roundtrip

BASE = "".join(f"line {n}\n" for n in range(1, 11))
TWICE = "same\nsame\n"


@dataclass(frozen=True)
class Step:
    """One scenario: what was attempted, what came back, and whether it held."""

    scenario: str
    lines: tuple[str, ...]
    ok: bool

    def render(self) -> str:
        verdict = "as advertised" if self.ok else "NOT AS ADVERTISED"
        body = "".join(f"  {line}\n" for line in self.lines)
        return f"{self.scenario:<38} {verdict}\n{body}"


def _refusal(action) -> tuple[str, bool]:
    try:
        action()
    except DiffError as error:
        return f"{type(error).__name__}: {error}", True
    return "no refusal", False


def _roundtrip() -> Step:
    edited = BASE.replace("line 4\n", "line four\n")
    verdict = roundtrip(BASE, edited)
    lines = verdict.lines()
    lines.append("every claim above is a computation, not a comment")
    return Step("the round trip holds", tuple(lines), verdict.ok)


def _ambiguous() -> Step:
    patch = parse_patch(_hand_patch("@@ -5 +5 @@\n-same\n+other\n"))
    message, held = _refusal(lambda: apply_text(TWICE, patch))
    lines = [
        "the patch says line 5; this text has two matching blocks at lines 1 and 2",
        message,
        "refusing is the point: picking the first would silently edit the wrong block",
    ]
    return Step("a hunk that matches twice", tuple(lines), held and "matches at" in message)


def _shifted() -> Step:
    patch = parse_patch(_hand_patch("@@ -3,2 +3,2 @@\n line 5\n-line 6\n+line six\n"))
    applied: Applied = apply_text(BASE, patch)
    moved = applied.text.index("line six")
    line_number = applied.text[:moved].count("\n") + 1
    lines = [
        f"{applied.line()}",
        f"the hunk said line 3; the context was found at line 5 ({line_number})",
        "each hunk is remeasured against the text it lands on, so earlier edits do not "
        "make later hunks miss",
    ]
    return Step("a hunk whose lines have moved", tuple(lines),
                line_number == 6 and not applied.fuzzy)


def _changed_context() -> Step:
    patch = parse_patch(_hand_patch("@@ -1,2 +1,2 @@\n line 1\n-line 2\n+line two\n"))
    message, held = _refusal(lambda: apply_text(BASE.replace("line 1", "start"), patch))
    lines = [message, "a patch that does not fit is not a patch to force"]
    return Step("a context line that changed", tuple(lines), held and "line 1 is" in message)


def _fuzz() -> Step:
    patch = parse_patch(_hand_patch("@@ -1,3 +1,3 @@\n line 1\n-line 2\n+line two\n line 3\n"))
    edited = BASE.replace("line 3", "line three")
    message, held = _refusal(lambda: apply_text(edited, patch))
    applied = apply_text(edited, patch, fuzz=1)
    lines = [
        f"strict: {message}",
        f"fuzz=1: {applied.line()}",
        "the tolerated line is kept from the file, not from the patch: "
        f"{applied.text.splitlines()[2]!r}",
        "fuzz is a report, not a silent repair, and this is why patch(1) says 'with fuzz'",
    ]
    return Step("fuzz hides a context edit", tuple(lines),
                held and applied.fuzzy and applied.text.splitlines()[2] == "line three")


def _no_newline() -> Step:
    patch = diff_text("a\nb", "a\nc")
    text = format_patch(patch)
    applied = apply_text("a\nb", patch)
    lines = [
        f"the patch carries the marker: {text.splitlines()[-1]!r}",
        f"applying it gives {applied.text!r} — no newline invented, none dropped",
        "a diff that cannot tell 'a\\n' from 'a' rewrites the last line of every file",
    ]
    return Step("no newline at end of file", tuple(lines),
                applied.text == "a\nc" and "No newline" in text)


def _twice() -> Step:
    patch = diff_text(BASE, BASE.replace("line 7\n", "line seven\n"))
    once = apply_text(BASE, patch).text
    message, held = _refusal(lambda: apply_text(once, patch))
    lines = [
        "applying a patch once is the normal case; applying it twice is the accident",
        message,
        "the second run refuses because the text it expected is gone — which is exactly "
        "the check that catches a retried deployment step",
    ]
    return Step("the same patch applied twice", tuple(lines), held)


def _hand_patch(body: str):
    return f"--- a\n+++ b\n{body}"


SCENARIOS = (_roundtrip, _ambiguous, _shifted, _changed_context, _fuzz, _no_newline, _twice)


def run() -> list[Step]:
    return [scenario() for scenario in SCENARIOS]


def render(steps: list[Step]) -> str:
    missed = sum(1 for step in steps if not step.ok)
    body = "\n".join(step.render() for step in steps)
    return f"{body}\ndemo: {len(steps)} scenarios, {missed} not as advertised"


def payload(steps: list[Step]) -> dict[str, object]:
    return {
        "ok": all(step.ok for step in steps),
        "scenarios": [{"scenario": step.scenario, "ok": step.ok,
                       "lines": list(step.lines)} for step in steps],
    }
