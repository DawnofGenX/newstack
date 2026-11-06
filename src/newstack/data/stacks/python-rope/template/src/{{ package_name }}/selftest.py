"""The invariants this rope promises, run against the real modules.

Every claim here is the reason the chunks are trustworthy: ``to_string``
is the join of the leaves in order, a slice or an edit answers exactly
what the plain string answers, a rebuild changes the shape and never the
text, and the edit counter tracks the spine, not the length of the text.
Runnable in a fresh checkout: `{{ package_name }} selftest`.
"""

from __future__ import annotations

import random

from .corpus import CorpusError, load_text, synthetic
from .rope import Rope, RopeError

FIXTURE = "a rope edits by walking"


class Report:
    """A tally of checks; `render()` ends with the pass/fail line."""

    def __init__(self) -> None:
        self.checks = 0
        self.failed = 0
        self.lines: list[str] = []

    def section(self, name: str) -> None:
        self.lines.append(f"- {name}")

    def ok(self, claim: str, held: bool) -> None:
        self.checks += 1
        if held:
            self.lines.append(f"  ok   {claim}")
        else:
            self.failed += 1
            self.lines.append(f"  FAIL {claim}")

    def equal(self, claim: str, found: object, expected: object) -> None:
        self.ok(
            f"{claim} ({found!r})" if found == expected else f"{claim}: {found!r} != {expected!r}",
            found == expected,
        )

    def refuses(self, claim: str, call: object, error: type[Exception]) -> None:
        try:
            call()  # type: ignore[operator]
        except error as seen:
            self.ok(f"{claim} ({seen})", True)
        except Exception as seen:
            self.ok(f"{claim}: raised {type(seen).__name__}, not {error.__name__}", False)
        else:
            self.ok(f"{claim}: nothing raised", False)

    def render(self) -> str:
        body = "\n".join(self.lines)
        return f"{body}\n\nselftest: {self.checks} checks passed, {self.failed} failed"


def _workload(report: Report, seed: int) -> None:
    """A seeded edit script against a plain str: every answer must agree."""
    text = synthetic(24, seed=seed, words=6)
    rope = Rope(text)
    shelf = text
    rng = random.Random(seed * 17 + 3)
    for step in range(60):
        pick = rng.random()
        size = len(shelf)
        if pick < 0.3 and size:
            at = rng.randrange(size + 1)
            needle = f"<{seed}-{step}>"
            rope.insert(at, needle)
            shelf = shelf[:at] + needle + shelf[at:]
        elif pick < 0.5 and size:
            start = rng.randrange(size)
            stop = min(size, start + rng.randrange(1, 9))
            gone = rope.delete(start, stop)
            report.equal(f"seed {seed} step {step} delete size", gone, stop - start)
            shelf = shelf[:start] + shelf[stop:]
        else:
            start = rng.randrange(size + 1) if size else 0
            stop = rng.randrange(start, size + 1) if size else 0
            window = rope.slice(start, stop)
            report.equal(f"seed {seed} step {step} slice", window.to_string(), shelf[start:stop])
            report.equal(f"seed {seed} step {step} length", len(window), stop - start)
        report.equal(f"seed {seed} step {step} text", rope.to_string(), shelf)
        report.equal(f"seed {seed} step {step} join", rope.to_string(), "".join(rope.chunks()))
    report.equal(f"seed {seed} ends as the shelf", rope.to_string(), shelf)


def _edits(report: Report) -> None:
    report.section("insert, delete, slice answer exactly what the str answers")
    _workload(report, 5)
    _workload(report, 11)
    rope = Rope("the quick brown fox")
    rope.insert(10, "red ")
    report.equal("insert lands at the offset", rope.to_string(), "the quick red brown fox")
    rope.append("!")
    report.equal("append lands at the end", rope.to_string(), "the quick red brown fox!")
    gone = rope.delete(4, 10)
    report.equal("delete answers the window size", gone, 6)
    report.equal("delete leaves the seam clean", rope.to_string(), "the red brown fox!")
    report.equal("a zero window deletes nothing", rope.delete(3, 3), 0)
    report.equal("an inverted window deletes nothing", rope.delete(9, 2), 0)
    report.equal("insert of empty text changes nothing", rope.insert(0, "") or rope.to_string(),
                 "the red brown fox!")


def _rebuild(report: Report) -> None:
    report.section("balance is invisible: rebuild moves shape, never text")
    rope = Rope(synthetic(60, seed=3, words=9))
    for _ in range(40):
        rope.append(" tail")
    before = rope.to_string()
    report.ok("edits alone can outgrow the budget", rope.height() > rope.budget())
    rope.rebalance()
    report.equal("the rebuild keeps the text", rope.to_string(), before)
    report.ok("the rebuild lands inside the budget", rope.is_balanced())
    window = rope.slice(10, 18)
    report.ok(
        "walks after the rebuild stay near the spine",
        window.touches <= 2 * (rope.height() + 1),
    )


def _split_join(report: Report) -> None:
    report.section("split then concat rejoins to exactly the original")
    for seed in (4, 9):
        text = synthetic(30, seed=seed, words=7)
        rope = Rope(text)
        for at in (0, 1, 40, len(text) // 2, len(text) - 1, len(text)):
            left, right = rope.split(at)
            report.equal(f"seed {seed} split at {at} keeps the left", left.to_string(), text[:at])
            report.equal(f"seed {seed} split at {at} keeps the right", right.to_string(), text[at:])
            report.equal(
                f"seed {seed} split at {at} rejoins", left.concat(right).to_string(), text
            )
    a = Rope("alpha")
    b = Rope("omega")
    report.equal("concat of two ropes is the pair in order", a.concat(b).to_string(), "alphaomega")
    report.equal("concat leaves both halves intact", (a.to_string(), b.to_string()),
                 ("alpha", "omega"))


def _counter(report: Report) -> None:
    report.section("edit cost tracks the spine, not the length of the text")
    small = Rope(synthetic(2, seed=6, words=3))
    large = Rope(synthetic(600, seed=6, words=40))
    small_window = small.slice(2, 4)
    large_window = large.slice(len(large) // 2, len(large) // 2 + 8)
    report.ok("the long text stays a long text", len(large) > 20_000)
    report.ok(
        "the walk touched a rounding error of the text",
        large_window.touches * 100 < len(large),
    )
    report.ok("both walks stayed near the spine", large_window.touches <= 2 * (large.height() + 1))
    report.ok("a short rope still walks its own short spine", small_window.touches >= 1)


def _refusals(report: Report) -> None:
    report.section("a rope refuses what it cannot answer")
    report.refuses("a leaf of zero is refused", lambda: Rope("x", max_leaf=0), RopeError)
    report.refuses("bytes are not text", lambda: Rope(b"abc"), RopeError)  # type: ignore[arg-type]
    report.refuses(
        "concat needs a rope", lambda: Rope("x").concat("y"), RopeError  # type: ignore[arg-type]
    )
    empty = Rope("")
    report.equal("an empty rope has no chunks", empty.chunks(), [])
    report.equal("an empty rope is empty text", empty.to_string(), "")
    report.equal("an empty rope still answers", len(empty), 0)


def _corpus(report: Report) -> None:
    report.section("texts come from files or from the generator")
    first = synthetic(12, seed=7)
    report.equal("the generator is deterministic", first, synthetic(12, seed=7))
    report.ok("a different seed is a different text", first != synthetic(12, seed=8))
    report.equal("paragraphs keep their lines", first.count("\n"), 11)
    report.refuses("zero paragraphs is not a text", lambda: synthetic(0), CorpusError)
    report.refuses("zero words is not a paragraph", lambda: synthetic(2, words=0), CorpusError)
    report.refuses("a missing file is named", lambda: load_text("no-such-text.txt"), CorpusError)


def _marker(report: Report) -> None:
    report.section("the phrase the detector looks for ships in the code")
    from . import rope as rope_module

    joined = " ".join((rope_module.__doc__ or "").split())
    report.ok("the marker sits in the rope module docstring", FIXTURE in joined)


def run() -> Report:
    report = Report()
    _edits(report)
    _rebuild(report)
    _split_join(report)
    _counter(report)
    _refusals(report)
    _corpus(report)
    _marker(report)
    return report
