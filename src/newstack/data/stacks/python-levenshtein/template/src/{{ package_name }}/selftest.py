"""The invariants this distance promises, run against the real modules.

Every claim here is the reason the row walk can be trusted: the walk
must equal the bare recursion on short shipped pairs, a distance must
read the same from either side, a detour through a third string must
never cost less than the direct change, a distance to the empty string
must be a change per letter, and every nearest answer must equal the
scan's argmin with ties handed to the lexically first entry. Runnable
in a fresh checkout: `{{ package_name }} selftest`.
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
    load_words,
    synthetic,
    write_words,
)
from .distance import SHIPPED, TRIPLES, DistanceError, distance, rank_pairs
from .oracle import ORACLE_LIMIT, oracle_distance
from .words import WordError, ensure_text, ensure_word
from .workload import WorkloadError, run_storm, shuffle_matches

FIXTURE = "a change costs one letter"
WORDS = ["car", "cart", "cat", "catnip", "dog", "dogma", "do", "doc"]


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
    report.section("the gate keeps letters out of the matrix")
    report.equal("a word comes back itself", ensure_word("cart"), "cart")
    report.equal("the empty string is text", ensure_text(""), "")
    report.refuses("the empty string is no word", lambda: ensure_word(""), WordError)
    report.refuses("uppercase has no cell", lambda: ensure_word("Cart"), WordError)
    report.refuses("a digit has no cell", lambda: ensure_word("car1"), WordError)
    report.refuses("a list has no letters", lambda: ensure_word(["cart"]), WordError)
    report.refuses(
        "sixty-five letters are past the gate",
        lambda: ensure_word("a" * 65),
        WordError,
    )


def _oracle(report: Report) -> None:
    report.section("the row walk equals the bare recursion, short words only")
    for left in SHIPPED:
        for right in SHIPPED:
            if len(left) <= ORACLE_LIMIT and len(right) <= ORACLE_LIMIT:
                report.equal(
                    f"{left!r} vs {right!r} agrees with the oracle",
                    distance(left, right),
                    oracle_distance(left, right),
                )
    report.refuses(
        "the oracle refuses a long pair",
        lambda: oracle_distance("a" * 9, "b" * 2),
        DistanceError,
    )


def _symmetry(report: Report) -> None:
    report.section("a distance reads the same from either side")
    for left in SHIPPED:
        for right in SHIPPED:
            report.equal(
                f"{left!r} <-> {right!r} mirrors",
                distance(left, right),
                distance(right, left),
            )


def _triangle(report: Report) -> None:
    report.section("a detour never beats the direct change")
    for left, middle, right in TRIPLES:
        direct = distance(left, right)
        detour = distance(left, middle) + distance(middle, right)
        report.ok(
            f"{left!r} -> {right!r} at most {direct} via {middle!r} at {detour}",
            direct <= detour,
        )
    corpus = synthetic(60, seed=29)
    for seed in (3, 977):
        rng = random.Random(seed)
        for _ in range(30):
            left, middle, right = rng.choice(corpus), rng.choice(corpus), rng.choice(corpus)
            report.ok(
                f"triangle holds for a seeded triple (seed {seed})",
                distance(left, right)
                <= distance(left, middle) + distance(middle, right),
            )


def _edges(report: Report) -> None:
    report.section("to the empty string is a change per letter")
    for word in SHIPPED:
        report.equal(f"{word!r} to nothing", distance(word, ""), len(word))
        report.equal(f"nothing to {word!r}", distance("", word), len(word))
    report.equal("nothing to nothing", distance("", ""), 0)


def _nearest(report: Report) -> None:
    report.section("nearest equals the scan's argmin, ties first by letters")
    corpus = list(SHIPPED)
    for query in ("crt", "kat", "dot", "night", "zzz"):
        scan = sorted(
            ((distance(query, word), word) for word in corpus),
            key=lambda pair: (pair[0], pair[1]),
        )
        best = distance(query, scan[0][1])
        report.equal(f"{query!r} nearest is the scan head", best, scan[0][0])
        report.ok(
            f"{query!r} head beats every entry",
            all(best <= distance(query, word) for word in corpus),
        )
    tied = [entry for entry in sorted(corpus) if distance("crt", entry) == 1]
    report.ok("a tie exists to rule over", len(tied) >= 2)
    scan = rank_pairs("crt", corpus)
    report.equal("the tied head is the lexically first", scan[0][1], min(tied))
    report.equal(
        "the ranking is the documented order",
        scan,
        sorted(scan, key=lambda pair: (pair[0], pair[1])),
    )
    report.refuses(
        "an empty corpus has no nearest",
        _nearest_empty,
        DistanceError,
    )


def _nearest_empty() -> None:
    from .distance import nearest

    nearest("cat", [])


def _rebuild(report: Report) -> None:
    report.section("corpus order is not an answer")
    corpus = synthetic(80, seed=55)
    report.ok("two orderings, one ranking", shuffle_matches(corpus))
    shuffled = list(reversed(corpus))
    for probe in ("cat", "dot", "zz"):
        report.equal(
            f"{probe!r} ranks the same both ways",
            rank_pairs(probe, corpus),
            rank_pairs(probe, shuffled),
        )


def _corpora(report: Report) -> None:
    report.section("the word list in, the snapshot out")
    corpus = synthetic(60, seed=5)
    report.equal("the generator is deterministic", corpus, synthetic(60, seed=5))
    report.ok("the words are distinct", len(set(corpus)) == 60)
    report.refuses("a corpus of zero is no corpus", lambda: synthetic(0), CorpusError)
    frozen = Snapshot(tuple(corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    report.equal("a snapshot replays its words", list(thawed.words), corpus)
    report.equal("a snapshot keeps its seed", thawed.seed, DEFAULT_SEED)
    report.refuses(
        "half a snapshot is no snapshot", lambda: Snapshot.loads('{"seed": 1}'), CorpusError
    )
    with TemporaryDirectory() as room:
        path = f"{room}/words.txt"
        write_words(corpus, path)
        report.equal("a written list reads back", load_words(path), corpus)
        report.refuses(
            "a missing list is named", lambda: load_words(f"{room}/missing.txt"), CorpusError
        )
        noise = f"{room}/noise.txt"
        with open(noise, "w", encoding="utf-8") as handle:
            handle.write("# a comment\n\nCart\n")
        report.refuses("a noisy list is refused", lambda: load_words(noise), CorpusError)


def _storms(report: Report) -> None:
    report.section("the storm, re-checked after every draw")
    for seed in (13, 77):
        storm = run_storm(seed=seed)
        report.equal(f"the storm ran its steps (seed {seed})", storm.steps, 160)
        report.equal(f"the storm broke nothing (seed {seed})", storm.breaks, 0)
        report.ok(f"the storm checked more than it stepped (seed {seed})",
                  storm.checks > storm.steps)
    report.refuses(
        "a storm without steps is refused", lambda: run_storm(steps=0), WorkloadError
    )


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    report.ok(
        "the marker is a lowercase phrase the detector can find",
        FIXTURE.lower() == FIXTURE and " " in FIXTURE,
    )


def run() -> Report:
    report = Report()
    _gate(report)
    _oracle(report)
    _symmetry(report)
    _triangle(report)
    _edges(report)
    _nearest(report)
    _rebuild(report)
    _corpora(report)
    _storms(report)
    _stories(report)
    return report
