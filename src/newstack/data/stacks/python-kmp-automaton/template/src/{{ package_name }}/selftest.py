"""The invariants this automaton promises, run against the real modules.

Every claim here is the reason the starts can be trusted: the
failure table must equal the naive border count state by state, the
scan's start list must equal the naive scan's on seeded corpora,
overlaps must be counted, and the empty pattern and the
longer-than-text edges must answer honestly. Runnable in a fresh
checkout: `python -m the-package selftest`.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
from .automaton import (
    AutomatonError,
    KmpAutomaton,
    failure_table,
    scan_starts,
)
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_patterns,
    synthetic,
    write_patterns,
)
from .naive import border_length, naive_count, naive_starts
from .pattern import MAX_PATTERN, PatternError, ensure_pattern, ensure_text

FIXTURE = "the failure link never forgets a border"
PATTERNS = ("a", "ab", "aa", "ana", "abra", "anana", "abab", "banana", "aabaaa")
TEXTS = (
    "",
    "a",
    "abracadabra",
    "bananabanaban",
    "aaaaaaaaaa",
    "abcababcabcab",
)


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
    report.section("the gate keeps lowercase in and noise out")
    report.equal("a pattern comes back itself", ensure_pattern("abra"), "abra")
    report.equal("the empty pattern is legal", ensure_pattern(""), "")
    report.refuses("an uppercase pattern is no pattern", lambda: ensure_pattern("Abra"),
                   PatternError)
    report.refuses("digits are no pattern", lambda: ensure_pattern("ab1"), PatternError)
    report.refuses("a space is no text", lambda: ensure_text("a b"), PatternError)
    report.refuses("a non-string is no pattern", lambda: ensure_pattern(7), PatternError)
    report.refuses(
        "one past the ceiling is no pattern",
        lambda: ensure_pattern("a" * (MAX_PATTERN + 1)),
        PatternError,
    )


def _table(report: Report) -> None:
    report.section("the failure table is the border count, state by state")
    for pattern in PATTERNS:
        table = failure_table(pattern)
        honest = tuple(border_length(pattern[:state]) for state in range(len(pattern) + 1))
        report.equal(f"{pattern!r} table is the borders", table, honest)
        report.equal(f"{pattern!r} audit clean", KmpAutomaton(pattern).audit(), [])
    report.equal("the empty pattern owns one link", failure_table(""), (0,))
    report.refuses("a loud pattern has no table", lambda: failure_table("Abra"),
                   AutomatonError)


def _starts(report: Report) -> None:
    report.section("the starts are the naive scan's starts, exactly")
    for text in TEXTS:
        for pattern in PATTERNS:
            found = scan_starts(text, pattern)
            owed = naive_starts(text, pattern)
            if found != owed:
                report.equal(f"{pattern!r} in {text!r} broke", "break", "none")
                return
    report.ok("every shipped pattern in every shipped text answered alike", True)
    corpus = synthetic(40, seed=23)
    for pattern in corpus:
        for text in ("abracadabra" * 2, "banana" * 3, "a" * 12):
            if scan_starts(text, pattern) != naive_starts(text, pattern):
                report.equal(f"corpus {pattern!r} broke", "break", "none")
                return
    report.ok("a seeded corpus answered like the naive scan, pattern after pattern", True)


def _overlaps(report: Report) -> None:
    report.section("overlaps are counted, not skipped")
    automaton = KmpAutomaton("ana")
    report.equal("ana in banana starts twice", automaton.find_all("banana"), [1, 3])
    report.equal("the count sees both", automaton.count("banana"), 2)
    report.equal("naive agrees on the overlap", naive_count("banana", "ana"), 2)
    report.equal("first is the leftmost", automaton.find_first("banana"), 1)
    report.equal("anana in banananananas rides every start",
                 KmpAutomaton("anana").find_all("banananananas"), [1, 3, 5, 7])
    report.equal("aa in aaaa rides every odd start", scan_starts("aaaa", "aa"), [0, 1, 2])


def _edges(report: Report) -> None:
    report.section("empty patterns and long patterns answer honestly")
    empty = KmpAutomaton("")
    report.equal("the empty pattern sits at every position", empty.count("abra"), 5)
    report.equal("the empty pattern in empty text", empty.find_all(""), [0])
    report.equal("the empty first start is zero", empty.find_first("abra"), 0)
    long_pattern = "abracadabra" + "cadabra"
    absent = KmpAutomaton(long_pattern)
    report.equal("a long pattern never sits", absent.find_all("abra"), [])
    report.equal("the count of an absent pattern", absent.count("abra"), 0)
    report.equal("the first of an absent pattern", absent.find_first("abra"), None)
    report.equal("the empty text holds nothing but empty", scan_starts("", "a"), [])
    report.refuses("a loud scan is refused", lambda: scan_starts("ABRA", "a"),
                   AutomatonError)


def _corpora(report: Report) -> None:
    report.section("the pattern list in, the snapshot out")
    corpus = synthetic(20, seed=5)
    report.equal("the generator is deterministic", corpus, synthetic(20, seed=5))
    report.ok("the patterns are distinct", len(set(corpus)) == 20)
    report.refuses("no patterns from zero", lambda: synthetic(0), CorpusError)
    frozen = Snapshot(tuple(corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    report.equal("a snapshot replays its patterns", list(thawed.patterns), corpus)
    report.refuses(
        "half a snapshot is no snapshot", lambda: Snapshot.loads('{"seed": 1}'), CorpusError
    )
    with TemporaryDirectory() as room:
        path = f"{room}/patterns.txt"
        write_patterns(corpus, path)
        report.equal("a written list reads back", load_patterns(path), corpus)
        report.refuses(
            "a missing list is named", lambda: load_patterns(f"{room}/missing.txt"),
            CorpusError,
        )
        noise = f"{room}/noise.txt"
        with open(noise, "w", encoding="utf-8") as handle:
            handle.write("# a comment\n\nAbra\n")
        report.refuses("a noisy list is refused", lambda: load_patterns(noise), CorpusError)


def _storms(report: Report) -> None:
    report.section("the storm, start against start")
    from .workload import (
        WorkloadError,
        rebuild_matches,
        run_storm,
    )

    for seed in (13, 77):
        storm = run_storm(seed=seed)
        report.equal(f"the storm ran its steps (seed {seed})", storm.steps, 140)
        report.equal(f"the storm broke nothing (seed {seed})", storm.breaks, ())
        report.ok(f"the storm held (seed {seed})", storm.seated)
        report.ok(
            f"the storm checked as much as it stepped (seed {seed})",
            storm.checks >= storm.steps,
        )
    report.ok("rebuilt tables answer alike", rebuild_matches(list(PATTERNS), list(TEXTS)))
    report.refuses(
        "a storm without steps is refused", lambda: run_storm(steps=0), WorkloadError
    )


def _tangles(report: Report) -> None:
    report.section("the tangle: a random walk, answered twice")
    for seed in (5, 31):
        rng = random.Random(seed)
        alphabet = "abnara"
        broke = False
        for _ in range(80):
            text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 24)))
            pattern = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 5)))
            if scan_starts(text, pattern) != naive_starts(text, pattern):
                broke = True
                break
        report.ok(f"eighty tangles answered alike (seed {seed})", not broke)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import automaton as automaton_module

    report.ok(
        "the marker the detector looks for is in the automaton module",
        FIXTURE in " ".join((automaton_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _gate(report)
    _table(report)
    _starts(report)
    _overlaps(report)
    _edges(report)
    _corpora(report)
    _storms(report)
    _tangles(report)
    _stories(report)
    return report
