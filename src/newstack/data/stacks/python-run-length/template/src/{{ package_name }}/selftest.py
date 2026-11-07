"""The invariants this counter promises, run against the real modules.

Every claim here is the reason the loop can be trusted: decode
must hand back the letters encode was sent, on shipped and seeded
corpora; encode must answer exactly what the stepper walks; a
repeat must cost strictly fewer pairs than letters; a stand past
the ceiling must split without losing length; and the empty text
and the loud strings must answer honestly. Runnable in a fresh
checkout: `python -m the-package selftest`.
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
    load_texts,
    report_lines,
    synthetic,
    write_texts,
)
from .naive import (
    naive_collapse,
    naive_decode,
    naive_encode,
    naive_price,
    naive_roundtrip,
)
from .pairs import (
    MAX_RUN,
    Pair,
    PairsError,
    pairs_from_json,
    pairs_to_json,
    walk_runs,
)
from .rle import (
    RunError,
    audit,
    decode,
    encode,
)
from .text import MAX_TEXT, TextError, ensure_text

FIXTURE = "a run is walked once and answered as a pair"
TEXTS = (
    "",
    "a",
    "ab",
    "abracadabra",
    "bananabananabana",
    "mississippimississippi",
    "aaaaaaaaaaaaaaaaaaaaaaaa",
    "abcabcabcabcabcabcabc",
)
REPEATS = ("abracadabbra" * 3, "baanana" * 6, "a" * 48, "mississippi" * 4)


@dataclass
class Report:
    checks: int = 0
    failed: int = 0
    lines: list = field(default_factory=list)

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

    def refuses(self, claim: str, call: object, error: type) -> None:
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
    report.equal("a text comes back itself", ensure_text("abra"), "abra")
    report.equal("the empty text is legal", ensure_text(""), "")
    report.refuses("an uppercase text is no text", lambda: ensure_text("Abra"), TextError)
    report.refuses("digits are no text", lambda: ensure_text("ab1"), TextError)
    report.refuses("a space is no text", lambda: ensure_text("a b"), TextError)
    report.refuses("a non-string is no text", lambda: ensure_text(7), TextError)
    report.refuses(
        "one past the ceiling is no text",
        lambda: ensure_text("a" * (MAX_TEXT + 1)),
        TextError,
    )


def _pairs(report: Report) -> None:
    report.section("a pair is a letter and an honest count")
    report.equal("a pair carries its letter", Pair("a", 3).letter, "a")
    report.equal("a run of one is an honest pair", Pair("a", 1).count, 1)
    report.refuses("an uppercase letter is refused", lambda: Pair("A", 1), PairsError)
    report.refuses("a zero count is refused", lambda: Pair("a", 0), PairsError)
    report.refuses("a past-ceiling count is refused", lambda: Pair("a", MAX_RUN + 1),
                   PairsError)
    stream = [Pair("a", 3), Pair("b", 1)]
    report.equal("a stream survives JSON", pairs_from_json(pairs_to_json(stream)), stream)
    report.refuses("half a row is no stream", lambda: pairs_from_json('[["a"]]'), PairsError)
    report.refuses("noise is no stream", lambda: pairs_from_json("noise"), PairsError)


def _stepper(report: Report) -> None:
    report.section("the stepper walks, encode answers")
    for text in TEXTS:
        if encode(text) != list(walk_runs(text)):
            report.equal(f"{text!r} did not match the stepper", "break", "none")
            return
    report.ok("encode answered the stepper on every shipped text", True)
    broken = "".join(
        pair.letter for pair in walk_runs("aaabbbcc")
    )
    report.equal("the collapsed view is the walk", broken, "abc")
    report.equal("the oracle collapses the same way", naive_collapse("aaabbbcc"), "abc")


def _loop(report: Report) -> None:
    report.section("decode hands back the letters encode was sent")
    for text in TEXTS:
        if decode(encode(text)) != text:
            report.equal(f"{text!r} did not survive the loop", "break", "none")
            return
        if audit(encode(text)):
            report.equal(f"{text!r} audited loud", "break", "none")
            return
    report.ok("every shipped text closed the loop, audit silent", True)
    corpus = synthetic(40, seed=23)
    for text in corpus:
        if decode(encode(text)) != text:
            report.equal(f"corpus {text!r} broke the loop", "break", "none")
            return
    report.ok("a seeded corpus closed the loop, text after text", True)


def _ceiling(report: Report) -> None:
    report.section("a stand past the ceiling splits, the sum stays")
    for size in (MAX_RUN, MAX_RUN + 1, MAX_RUN * 3 + 7):
        run = "z" * size
        pairs = encode(run)
        total = sum(pair.count for pair in pairs)
        if decode(pairs) != run or total != size:
            report.equal(f"a stand of {size} lost letters", "break", "none")
            return
        if any(pair.count > MAX_RUN for pair in pairs):
            report.equal(f"a stand of {size} breached the ceiling", "break", "none")
            return
    report.ok("stands at, past, and far past the ceiling stayed whole", True)
    report.equal("the ceiling is the documented one", MAX_RUN, 255)


def _pricing(report: Report) -> None:
    report.section("a repeat pays in pairs, never in letters")
    for text in REPEATS:
        if len(encode(text)) >= len(text):
            report.equal(f"{text[:16]!r}... cost letters, not pairs", "break", "none")
            return
    report.ok("every shipped repeat cost strictly fewer pairs than letters", True)
    for text in TEXTS:
        if len(encode(text)) > naive_price(text):
            report.equal(f"{text!r} outbid the naive price", "break", "none")
            return
    report.ok("no shipped text cost more than the naive price", True)
    report.equal("the naive price is one pair per letter", naive_price("abra"), 4)
    report.equal("the naive loop closes its own stream", naive_roundtrip("abra"), True)
    report.equal("the naive read folds a stream", naive_decode(naive_encode("abra")), "abra")


def _edges(report: Report) -> None:
    report.section("empty texts and single letters answer honestly")
    report.equal("the empty text streams empty", encode(""), [])
    report.equal("the empty stream reads empty", decode([]), "")
    report.equal("one letter is one honest pair", encode("a"), [Pair("a", 1)])
    report.equal("two letters are two honest pairs", len(encode("ab")), 2)
    report.equal("the audit of nothing is nothing", audit([]), [])
    report.refuses("a loud encode is refused", lambda: encode("ABRA"), TextError)
    report.refuses("a broken stream is refused on decode", lambda: decode([("a", 0)]),
                   RunError)


def _corpora(report: Report) -> None:
    report.section("the corpus in, the report out")
    corpus = synthetic(20, seed=5)
    report.equal("the generator is deterministic", corpus, synthetic(20, seed=5))
    report.ok("the texts are distinct", len(set(corpus)) == 20)
    report.refuses("no texts from zero", lambda: synthetic(0), CorpusError)
    frozen = Snapshot(tuple(corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    report.equal("a snapshot replays its texts", list(thawed.texts), corpus)
    report.refuses(
        "half a snapshot is no snapshot", lambda: Snapshot.loads('{"seed": 1}'),
        CorpusError,
    )
    with TemporaryDirectory() as room:
        path = f"{room}/corpora.txt"
        write_texts(corpus, path)
        report.equal("a written corpus reads back", load_texts(path), corpus)
        report.refuses(
            "a missing corpus is named", lambda: load_texts(f"{room}/missing.txt"),
            CorpusError,
        )
        noise = f"{room}/noise.txt"
        with open(noise, "w", encoding="utf-8") as handle:
            handle.write("# a comment\n\nAbra\n")
        report.refuses("a noisy corpus is refused", lambda: load_texts(noise), CorpusError)
    report.ok("the report counts every text", len(report_lines(TEXTS)) == len(TEXTS))


def _tangles(report: Report) -> None:
    report.section("the tangle: a random walk, closed twice")
    for seed in (5, 31):
        rng = random.Random(seed)
        broke = False
        for _ in range(80):
            letters = "".join(rng.choice("abnrz") for _ in range(rng.randint(1, 9)))
            text = letters + "".join(
                rng.choice("abnrz") * rng.randint(1, MAX_RUN + 30) for _ in range(3)
            )
            if decode(encode(text)) != text or audit(encode(text)):
                broke = True
                break
        report.ok(f"eighty tangles closed the loop (seed {seed})", not broke)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import rle as rle_module

    report.ok(
        "the marker the detector looks for is in the counter module",
        FIXTURE in " ".join((rle_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _gate(report)
    _pairs(report)
    _stepper(report)
    _loop(report)
    _ceiling(report)
    _pricing(report)
    _edges(report)
    _corpora(report)
    _tangles(report)
    _stories(report)
    return report
