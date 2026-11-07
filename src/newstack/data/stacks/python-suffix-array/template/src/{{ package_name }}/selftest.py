"""The invariants this table promises, run against the real modules.

Every claim here is the reason the starts can be trusted: the order
must equal the plain slice sort on seeded texts, every count must
equal the scan's start census (overlaps honest), the longest repeat
must be the tallest neighbour share, and the empty and single-letter
texts must answer without complaint. Runnable in a fresh checkout:
`{{ package_name }} selftest`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_texts,
    synthetic,
    write_texts,
)
from .scan import scan_array, scan_count, scan_lcp_array, scan_lcp_pair, scan_lrs
from .suffix import SuffixArray, SuffixError, build
from .text import TextError, ensure_pattern, ensure_text

FIXTURE = "a suffix is the text from one letter to the end"
TEXTS = ("banana", "mississippi", "abracadabra", "aaaa", "abcabcabc")


@dataclass
class Report:
    checks: int = 0
    failed: int = 0
    lines: list[str] = field(default_factory=list)

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
            f"{claim} ({found!r})"
            if found == expected
            else f"{claim}: {found!r} != {expected!r}",
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
        tail = f"selftest: {self.checks - self.failed} checks passed, {self.failed} failed"
        return "\n".join((*self.lines, "", tail))


def _gate(report: Report) -> None:
    report.section("the gate keeps letters in and noise out")
    report.equal("a text comes back itself", ensure_text("banana"), "banana")
    report.equal("the empty text passes", ensure_text(""), "")
    report.equal("a pattern comes back itself", ensure_pattern("nan"), "nan")
    report.refuses("the empty pattern is no pattern", lambda: ensure_pattern(""), TextError)
    report.refuses("uppercase has no place", lambda: ensure_text("Banana"), TextError)
    report.refuses("a digit has no place", lambda: ensure_text("ban3na"), TextError)
    report.refuses("a list is no text", lambda: ensure_text(["a"]), TextError)
    report.refuses(
        "a thousand twenty-five letters are past the gate",
        lambda: ensure_text("a" * 1025),
        TextError,
    )


def _order(report: Report) -> None:
    report.section("the order is the plain sort, exactly")
    for text in (TEXTS[0], "mississippi", synthetic(4, seed=31)[0]):
        table = SuffixArray(text)
        report.equal(f"{text!r} orders like slices", table.array, scan_array(text))
        report.ok(f"{text!r} stays seated", table.invariant())
        report.equal(f"{text!r} audits clean", table.audit(), [])
    corpus = synthetic(30, seed=17)
    report.ok(
        "thirty seeded texts order exactly",
        all(SuffixArray(body).array == scan_array(body) for body in corpus),
    )


def _count(report: Report) -> None:
    report.section("the count is every start, overlaps honest")
    for text in ("aaaa", "banana", "abcabcabc"):
        table = SuffixArray(text)
        for pattern in ("a", "aa", "aaa", text[:2], "zz"):
            report.equal(
                f"{pattern!r} in {text!r}", table.count(pattern), scan_count(text, pattern)
            )
    report.equal("an overlapping run counts every start", SuffixArray("aaaa").count("aa"), 3)
    report.ok(
        "the rule differs from str.count on overlaps",
        SuffixArray("aaaa").count("aa") == 3 and "aaaa".count("aa") == 2,
    )
    report.refuses("the empty pattern is refused", lambda: SuffixArray("a").count(""), TextError)


def _shares(report: Report) -> None:
    report.section("the shares sit where the neighbours meet")
    for text in TEXTS:
        table = SuffixArray(text)
        report.equal(f"{text!r} shares like the scan", table.lcp_array(), scan_lcp_array(text))
        for left, right in ((0, 1), (0, len(text) - 1), (2, 2)):
            if left < len(text) and right < len(text):
                report.equal(
                    f"{left},{right} of {text!r}",
                    table.lcp(left, right),
                    scan_lcp_pair(text, left, right),
                )
        report.equal(
            f"the repeat of {text!r} is the tall share",
            table.longest_repeat(),
            scan_lrs(text),
        )
    table = SuffixArray("banana")
    report.equal("a suffix shared with itself is its length", table.lcp(2, 2), 4)
    report.refuses("a place past the text is refused", lambda: table.lcp(0, 99), SuffixError)


def _edges(report: Report) -> None:
    report.section("empty and single letters answer without complaint")
    bare = SuffixArray("")
    report.equal("the empty table has no starts", bare.array, [])
    report.equal("the empty table has no shares", bare.lcp_array(), [])
    report.equal("the empty repeat is empty", bare.longest_repeat(), "")
    report.ok("the empty table is seated", bare.invariant())
    one = SuffixArray("a")
    report.equal("one letter starts at zero", one.array, [0])
    report.equal("one letter shares nothing", one.lcp_array(), [])
    report.equal("one letter repeats nothing", one.longest_repeat(), "")
    report.equal("a missing suffix is named", len(build("")), 0)


def _corpora(report: Report) -> None:
    report.section("the text list in, the snapshot out")
    corpus = synthetic(20, seed=5)
    report.equal("the generator is deterministic", corpus, synthetic(20, seed=5))
    report.ok("the texts are distinct", len(set(corpus)) == 20)
    report.refuses("no texts from zero", lambda: synthetic(0), CorpusError)
    frozen = Snapshot(tuple(corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    report.equal("a snapshot replays its texts", list(thawed.texts), corpus)
    report.refuses(
        "half a snapshot is no snapshot", lambda: Snapshot.loads('{"seed": 1}'), CorpusError
    )
    with TemporaryDirectory() as room:
        path = f"{room}/texts.txt"
        write_texts(corpus, path)
        report.equal("a written list reads back", load_texts(path), corpus)
        report.refuses(
            "a missing list is named", lambda: load_texts(f"{room}/missing.txt"), CorpusError
        )
        noise = f"{room}/noise.txt"
        with open(noise, "w", encoding="utf-8") as handle:
            handle.write("# a comment\n\nBanana\n")
        report.refuses("a noisy list is refused", lambda: load_texts(noise), CorpusError)


def _storms(report: Report) -> None:
    report.section("the storm, re-checked after every answer")
    from .workload import WorkloadError, rebuild_matches, run_storm

    for seed in (13, 77):
        storm = run_storm(seed=seed)
        report.equal(f"the storm ran its steps (seed {seed})", storm.steps, 140)
        report.equal(f"the storm broke nothing (seed {seed})", storm.breaks, 0)
        report.ok(f"the storm stayed seated (seed {seed})", storm.seated)
        report.ok(f"the storm checked more than it stepped (seed {seed})",
                  storm.checks > storm.steps)
    report.ok("rebuilt tables answer alike", rebuild_matches(list(TEXTS)))
    report.refuses("a storm without steps is refused", lambda: run_storm(steps=0),
                   WorkloadError)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import suffix as suffix_module

    report.ok(
        "the marker the detector looks for is in the table module",
        FIXTURE in " ".join((suffix_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _gate(report)
    _order(report)
    _count(report)
    _shares(report)
    _edges(report)
    _corpora(report)
    _storms(report)
    _stories(report)
    return report
