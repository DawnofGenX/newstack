"""Check this build against its own claims, without pytest and without a temp repo."""

from __future__ import annotations

from . import demo
from .apply import apply_text
from .diff import diff_lines, diff_text, format_patch, parse_patch
from .model import ApplyError, ParseError, split_lines
from .verify import roundtrip

BASE = "".join(f"line {n}\n" for n in range(1, 11))


class Checks:
    """A tiny assertion runner: no pytest in a wheel, and no silent skips."""

    def __init__(self) -> None:
        self.passed = 0
        self.failed: list[str] = []
        self.last: Exception | None = None

    def ok(self, description: str, condition: bool) -> None:
        if condition:
            self.passed += 1
        else:
            self.failed.append(description)

    def equal(self, description: str, want: object, got: object) -> None:
        self.ok(description, want == got)

    def raises(self, description: str, function, *args, **kwargs) -> None:
        try:
            function(*args, **kwargs)
        except (ParseError, ApplyError, ValueError) as error:
            self.passed += 1
            self.last = error
        else:
            self.failed.append(description)


def _splitting(checks: Checks) -> None:
    checks.equal("split keeps the newline", ["a\n", "b\n"], split_lines("a\nb\n"))
    checks.equal("split keeps a last line without one", ["a\n", "b"], split_lines("a\nb"))
    checks.equal("an empty text has no lines", [], split_lines(""))


def _headers(checks: Checks) -> None:
    single = diff_lines(["a\n"], ["b\n"])
    checks.equal("one changed line is one hunk", 1, len(single))
    checks.equal("a count of one is left out", "@@ -1 +1 @@", single[0].header())
    patch = parse_patch("--- a\n+++ b\n@@ -0,0 +1,2 @@\n+x\n+y\n")
    checks.equal("an empty old side comes from line 0", 0, patch.hunks[0].old_start)
    checks.equal("a count of two survives", "@@ -0,0 +1,2 @@", patch.hunks[0].header())


def _roundtrips(checks: Checks) -> None:
    for label, old, new in (
        ("an edit", BASE, BASE.replace("line 3\n", "line three\n")),
        ("an insertion", BASE, BASE.replace("line 5\n", "line 5\nnew\n")),
        ("a deletion", BASE, BASE.replace("line 6\n", "")),
        ("a rewrite", BASE, "".join(f"row {n}\n" for n in range(1, 22))),
        ("nothing", BASE, BASE),
        ("an empty file to a line", "", "only\n"),
        ("a line to an empty file", "only\n", ""),
    ):
        verdict = roundtrip(old, new)
        checks.ok(f"round trip holds: {label}", verdict.ok)


def _newlines(checks: Checks) -> None:
    patch = diff_text("a\nb", "a\nc")
    text = format_patch(patch)
    checks.ok("the marker is written once per side", text.count("No newline") == 2)
    checks.equal("applying keeps the missing newline", "a\nc", apply_text("a\nb", patch).text)
    added = format_patch(diff_text("a\n", "b\n"))
    checks.ok("a newline that exists produces no marker", "No newline" not in added)


def _refusals(checks: Checks) -> None:
    twice = "same\nsame\n"
    patch = parse_patch("--- a\n+++ b\n@@ -5 +5 @@\n-same\n+other\n")
    checks.raises("a hunk that matches twice is refused", apply_text, twice, patch)
    checks.ok("and the message names both places", "matches at lines 1 and 2"
              in str(getattr(checks, "last", "")))
    one = parse_patch("--- a\n+++ b\n@@ -1,2 +1,2 @@\n line 1\n-line 2\n+line two\n")
    checks.raises("a context that does not fit is refused", apply_text, "start\nline 2\n", one)
    once = apply_text(BASE, diff_text(BASE, BASE.replace("line 7\n", "line seven\n"))).text
    twice_patch = diff_text(BASE, BASE.replace("line 7\n", "line seven\n"))
    checks.raises("a patch applied twice is refused", apply_text, once, twice_patch)
    checks.raises("a negative fuzz is refused", apply_text, BASE, one, fuzz=-1)
    checks.raises("a negative context is refused", diff_lines, ["a\n"], ["b\n"], -1)


def _parse_errors(checks: Checks) -> None:
    bad = (
        ("no headers", "hello\n"),
        ("headers with no hunks", "--- a\n+++ b\n"),
        ("a count that lies", "--- a\n+++ b\n@@ -1,3 +1,1 @@\n-a\n+b\n"),
        ("a body line that is not a diff line", "--- a\n+++ b\n@@ -1 +1 @@\nx\n"),
        ("a missing +++ header", "--- a\n@@ -1 +1 @@\n-a\n+b\n"),
        ("a range that is not a number", "--- a\n+++ b\n@@ -x +1 @@\n-a\n+b\n"),
        ("a marker before any line", "--- a\n+++ b\n@@ -1 +1 @@\n\\ No newline at end of file\n"),
    )
    for label, text in bad:
        checks.raises(f"parse refuses {label}", parse_patch, text)
    written = diff_text(BASE, BASE + "extra\n")
    checks.equal("a patch survives a format/parse round trip", len(written.hunks),
                 len(parse_patch(format_patch(written)).hunks))


def _demo(checks: Checks) -> None:
    steps = demo.run()
    checks.equal("every scenario holds", 0, sum(1 for step in steps if not step.ok))
    checks.equal("there are seven of them", 7, len(steps))
    checks.ok("the footer counts none missed", "0 not as advertised" in demo.render(steps))


def run() -> int:
    checks = Checks()
    for group in (_splitting, _headers, _roundtrips, _newlines, _refusals, _parse_errors, _demo):
        group(checks)
    total = checks.passed + len(checks.failed)
    for description in checks.failed:
        print(f"FAIL  {description}")
    print(f"selftest: {checks.passed} checks passed, {len(checks.failed)} failed out of {total}")
    return 0 if not checks.failed else 1
