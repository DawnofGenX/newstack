"""The invariants this scanner promises, run against the real modules.

Every claim here is the reason the starts can be trusted: the roll
must equal a fresh weigh on every shipped window, the scan's start
list must equal the naive scan's on seeded corpora, collisions must
stay honest (candidates checked letter by letter), overlaps must be
counted, and the empty pattern and the longer-than-text edges must
answer honestly. Runnable in a fresh checkout: `python -m the-package
selftest`.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_patterns,
    synthetic,
    write_patterns,
)
from .hashing import (
    BASE,
    MODULUS,
    HashError,
    leading_power,
    letter_value,
    roll,
    window_hash,
    windows,
)
from .naive import naive_count, naive_starts
from .pattern import MAX_PATTERN, PatternError, ensure_pattern, ensure_text
from .scanner import RollingScanner, ScannerError, scan_starts

FIXTURE = "the rolling window never forgets a letter it is standing on"
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


def _hash(report: Report) -> None:
    report.section("the roll equals the fresh weigh, window after window")
    report.equal("letters weigh one to twenty-six", letter_value("z"), 26)
    report.equal("the empty window is weightless", window_hash(""), 0)
    report.refuses("a loud letter has no weight", lambda: letter_value("A"), HashError)
    report.equal("width one owns power one", leading_power(1), 1)
    report.refuses("no windows for width zero", lambda: windows("abra", 0), HashError)
    for width in (1, 2, 3, 5, 7):
        broke = ""
        for text in TEXTS:
            for start, window in enumerate(windows(text, width)):
                if start == 0:
                    continue
                rolled = roll(
                    window_hash(text[start - 1 : start - 1 + width]),
                    text[start - 1],
                    text[start - 1 + width],
                    width,
                )
                if rolled != window_hash(window):
                    broke = f"{window!r} at {start} in {text!r}"
                    break
            if broke:
                break
        report.equal(f"width {width} rolled windows answer to the weigh", broke, "")
    report.ok(
        "the base and modulus are the documented ones",
        BASE == 911 and MODULUS == 1_000_000_007,
    )
    report.equal(
        "ab and b never share a hash by position",
        window_hash("ab") != window_hash("b"),
        True,
    )


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


def _collisions(report: Report) -> None:
    report.section("collisions are honest: every candidate is checked")
    scanner = RollingScanner("abra")
    report.equal("the audit is silent on shipped texts", scanner.audit("abracadabra"), [])
    report.equal("an audit of a loud text is refused as no scan",
                 _quiet_audit(scanner, "ABRA"), "refused")
    tax = scanner.collisions("abracadabra" * 3)
    report.ok(f"the collision tax is a number, never a wrong start (tax {tax})", tax >= 0)
    for pattern in PATTERNS:
        check = RollingScanner(pattern)
        for text in TEXTS:
            if check.audit(text):
                report.equal(f"{pattern!r} audit broke on {text!r}", "break", "none")
                return
    report.ok("every shipped scanner audits silent on every shipped text", True)


def _quiet_audit(scanner: RollingScanner, text: str) -> str:
    try:
        scanner.audit(text)
    except (ScannerError, PatternError):
        return "refused"
    return "answered"


def _overlaps(report: Report) -> None:
    report.section("overlaps are counted, not skipped")
    scanner = RollingScanner("ana")
    report.equal("ana in banana starts twice", scanner.find_all("banana"), [1, 3])
    report.equal("the count sees both", scanner.count("banana"), 2)
    report.equal("naive agrees on the overlap", naive_count("banana", "ana"), 2)
    report.equal("first is the leftmost", scanner.find_first("banana"), 1)
    report.equal("anana in banananananas rides every start",
                 RollingScanner("anana").find_all("banananananas"), [1, 3, 5, 7])
    report.equal("aa in aaaa rides every start", scan_starts("aaaa", "aa"), [0, 1, 2])


def _edges(report: Report) -> None:
    report.section("empty patterns and long patterns answer honestly")
    empty = RollingScanner("")
    report.equal("the empty pattern sits at every position", empty.count("abra"), 5)
    report.equal("the empty pattern in empty text", empty.find_all(""), [0])
    report.equal("the empty first start is zero", empty.find_first("abra"), 0)
    long_pattern = "abracadabra" + "cadabra"
    absent = RollingScanner(long_pattern)
    report.equal("a long pattern never sits", absent.find_all("abra"), [])
    report.equal("the count of an absent pattern", absent.count("abra"), 0)
    report.equal("the first of an absent pattern", absent.find_first("abra"), None)
    report.equal("the empty text holds nothing but empty", scan_starts("", "a"), [])
    report.refuses("a loud scan is refused", lambda: scan_starts("ABRA", "a"),
                   ScannerError)
    report.refuses("a loud scanner is refused", lambda: RollingScanner("Abra"),
                   ScannerError)


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
        rerolled_answers,
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
    report.ok("rerolled scans answer alike", rerolled_answers(list(PATTERNS), list(TEXTS)))
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
    from . import scanner as scanner_module

    report.ok(
        "the marker the detector looks for is in the scanner module",
        FIXTURE in " ".join((scanner_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _gate(report)
    _hash(report)
    _starts(report)
    _collisions(report)
    _overlaps(report)
    _edges(report)
    _corpora(report)
    _storms(report)
    _tangles(report)
    _stories(report)
    return report
