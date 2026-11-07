"""The invariants this array promises, run against the real modules.

Every claim here is the reason the array can be trusted: the
Z-array must equal the naive per-position stepper entry by entry,
``z[0]`` must be the length of the word, the derived occurrence
list must equal the naive scan's start list on seeded corpora, and
the single-letter and empty-word edges must answer honestly.
Runnable in a fresh checkout: `python -m the-package selftest`.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
from .array import (
    SEP,
    ArrayError,
    ZArray,
    occurrences,
    z_function,
)
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_words,
    synthetic,
    write_words,
)
from .naive import lcp_length, naive_count, naive_occurrences, naive_z
from .word import MAX_WORD, WordError, ensure_pattern, ensure_word

FIXTURE = "the window never hands out a letter it has not matched"
WORDS = (
    "",
    "a",
    "aa",
    "ab",
    "ana",
    "abra",
    "anana",
    "abab",
    "banana",
    "aabaaa",
    "abracadabra",
    "aaaaaaaaaa",
)
PATTERNS = ("a", "ab", "aa", "ana", "abra", "anana", "abab", "banana", "aabaaa")


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
    report.equal("a word comes back itself", ensure_word("abra"), "abra")
    report.equal("the empty word is legal", ensure_word(""), "")
    report.equal("a pattern is a word by another name", ensure_pattern("ana"), "ana")
    report.refuses("an uppercase word is no word", lambda: ensure_word("Abra"), WordError)
    report.refuses("digits are no word", lambda: ensure_word("ab1"), WordError)
    report.refuses("a space is no word", lambda: ensure_word("a b"), WordError)
    report.refuses("a non-string is no word", lambda: ensure_word(7), WordError)
    report.refuses(
        "one past the ceiling is no word",
        lambda: ensure_word("a" * (MAX_WORD + 1)),
        WordError,
    )


def _array(report: Report) -> None:
    report.section("the array is the stepper's answer, entry by entry")
    for word in WORDS:
        cut = z_function(word)
        honest = naive_z(word)
        report.equal(f"{word!r} array is the scan", cut, honest)
        report.equal(f"{word!r} audit clean", ZArray(word).audit(), [])
        if cut:
            report.equal(f"{word!r} z[0] is its length", cut[0], len(word))
    report.equal("the empty word owns the empty array", z_function(""), ())
    report.equal("a single letter owns its length", z_function("a"), (1,))
    report.equal(
        "the stepper counts shared letters", lcp_length("anana", "abana"), 1
    )
    report.equal("the stepper of nothing", lcp_length("", "abra"), 0)
    report.refuses("a loud word has no array", lambda: z_function("Abra"), ArrayError)


def _occurrences(report: Report) -> None:
    report.section("the occurrences are the naive scan's starts, exactly")
    for word in WORDS:
        for pattern in PATTERNS:
            found = occurrences(word, pattern)
            owed = naive_occurrences(word, pattern)
            if found != owed:
                report.equal(f"{pattern!r} in {word!r} broke", "break", "none")
                return
    report.ok("every shipped pattern in every shipped word answered alike", True)
    report.equal("ana in banana starts twice", occurrences("banana", "ana"), [1, 3])
    report.equal("the count sees the overlap", naive_count("banana", "ana"), 2)
    report.equal("anana rides every start", occurrences("banananananas", "anana"),
                 [1, 3, 5, 7])
    report.equal("aa in aaaa rides every start", occurrences("aaaa", "aa"), [0, 1, 2])
    report.equal("the separator is no letter", SEP not in "abc", True)


def _edges(report: Report) -> None:
    report.section("empty words and long patterns answer honestly")
    report.equal("the empty pattern sits at every position", occurrences("abra", ""),
                 [0, 1, 2, 3, 4])
    report.equal("the empty pattern in the empty word", occurrences("", ""), [0])
    report.equal("a long pattern never sits", occurrences("abra", "abracadabra"), [])
    report.equal("the empty word holds nothing but empty", occurrences("", "a"), [])
    report.equal("a single letter finds itself", occurrences("a", "a"), [0])
    report.equal("the first of an absent pattern", ZArray("abra").first_of("cadabra"),
                 None)
    report.equal("abra in abracadabra sits twice",
                 ZArray("abracadabra").starts_of("abra"), [0, 7])
    report.refuses("a loud scan is refused", lambda: occurrences("ABRA", "a"),
                   ArrayError)


def _corpora(report: Report) -> None:
    report.section("the word list in, the snapshot out")
    corpus = synthetic(20, seed=5)
    report.equal("the generator is deterministic", corpus, synthetic(20, seed=5))
    report.ok("the words are distinct", len(set(corpus)) == 20)
    report.refuses("no words from zero", lambda: synthetic(0), CorpusError)
    frozen = Snapshot(tuple(corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    report.equal("a snapshot replays its words", list(thawed.words), corpus)
    report.refuses(
        "half a snapshot is no snapshot", lambda: Snapshot.loads('{"seed": 1}'),
        CorpusError,
    )
    with TemporaryDirectory() as room:
        path = f"{room}/words.txt"
        write_words(corpus, path)
        report.equal("a written list reads back", load_words(path), corpus)
        report.refuses(
            "a missing list is named", lambda: load_words(f"{room}/missing.txt"),
            CorpusError,
        )
        noise = f"{room}/noise.txt"
        with open(noise, "w", encoding="utf-8") as handle:
            handle.write("# a comment\n\nAbra\n")
        report.refuses("a noisy list is refused", lambda: load_words(noise), CorpusError)


def _storms(report: Report) -> None:
    report.section("the storm, entry against entry")
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
    report.ok("re-cut arrays answer alike", rebuild_matches(list(WORDS)))
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
            word = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 24)))
            pattern = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 5)))
            if z_function(word) != naive_z(word):
                broke = True
                break
            if occurrences(word, pattern) != naive_occurrences(word, pattern):
                broke = True
                break
        report.ok(f"eighty tangles answered alike (seed {seed})", not broke)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import array as array_module

    report.ok(
        "the marker the detector looks for is in the array module",
        FIXTURE in " ".join((array_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _gate(report)
    _array(report)
    _occurrences(report)
    _edges(report)
    _corpora(report)
    _storms(report)
    _tangles(report)
    _stories(report)
    return report
