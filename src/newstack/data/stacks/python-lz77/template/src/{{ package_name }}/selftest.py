"""The invariants this coder promises, run against the real modules.

Every claim here is the reason the loop can be trusted: the read
must hand back the letters the write was sent, on shipped and
seeded corpora; every quote must name letters the window already
emitted; a repeat must cost fewer tokens than letters; and the
empty text and the loud strings must answer honestly. Runnable in
a fresh checkout: `python -m the-package selftest`.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
from .coder import (
    MIN_MATCH,
    CoderError,
    audit,
    compress,
    decompress,
)
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
    naive_emit,
    naive_read,
    naive_roundtrip,
    naive_size,
)
from .text import MAX_TEXT, TextError, ensure_text
from .tokens import (
    MAX_MATCH,
    MAX_WINDOW,
    BackRef,
    Literal,
    TokenError,
    tokens_from_json,
    tokens_to_json,
)
from .workload import (
    WorkloadError,
    honest_streams,
    run_storm,
)

FIXTURE = "the sliding window never quotes a letter it has never emitted"
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
REPEATS = ("abracadabra" * 3, "banana" * 6, "a" * 48, "mississippi" * 4)


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


def _tokens(report: Report) -> None:
    report.section("a token is a letter or an honest quote")
    report.equal("a literal carries its letter", Literal("a").letter, "a")
    report.refuses("an uppercase literal is refused", lambda: Literal("A"), TokenError)
    report.refuses("a zero offset is refused", lambda: BackRef(0, 2), TokenError)
    report.refuses("a one-letter quote is refused", lambda: BackRef(2, 1), TokenError)
    report.refuses(
        "an offset past the window is refused",
        lambda: BackRef(MAX_WINDOW + 1, 2),
        TokenError,
    )
    report.refuses(
        "a quote past the ceiling is refused",
        lambda: BackRef(2, MAX_MATCH + 1),
        TokenError,
    )
    stream = [Literal("a"), BackRef(1, 2)]
    report.equal("a stream survives JSON", tokens_from_json(tokens_to_json(stream)), stream)
    report.refuses("half a row is no stream", lambda: tokens_from_json('[["b", 2]]'),
                   TokenError)
    report.refuses("noise is no stream", lambda: tokens_from_json("noise"), TokenError)


def _loop(report: Report) -> None:
    report.section("the read hands back the letters the write was sent")
    for text in TEXTS:
        tokens = compress(text)
        if decompress(tokens) != text:
            report.equal(f"{text!r} did not survive the loop", "break", "none")
            return
        if audit(tokens):
            report.equal(f"{text!r} quoted beyond the window", "break", "none")
            return
    report.ok("every shipped text survived the loop, audit silent", True)
    corpus = synthetic(40, seed=23)
    for text in corpus:
        if decompress(compress(text)) != text:
            report.equal(f"corpus {text!r} broke the loop", "break", "none")
            return
    report.ok("a seeded corpus closed the loop, text after text", True)


def _honest(report: Report) -> None:
    report.section("every quote names letters the window already emitted")
    for text in TEXTS:
        if audit(compress(text)):
            report.equal(f"{text!r} audit broke", "break", "none")
            return
    report.ok("every shipped stream audits silent", True)
    report.equal("the oracle closes its own loop", naive_roundtrip("abra"), True)
    report.equal("the naive read folds literals", naive_read(naive_emit("abra")), "abra")
    report.refuses(
        "a quote into nothing is refused",
        lambda: decompress([BackRef(3, 2)]),
        CoderError,
    )
    report.ok(
        "the window and ceiling are the documented ones",
        MAX_WINDOW == 4096 and MAX_MATCH == 32 and MIN_MATCH == 2,
    )
    broke = ""
    for size in (2, 5, 17, 32):
        quote = BackRef(size, size)
        stream = [Literal("a")] * size + [quote]
        folded = decompress(stream)
        if folded != "a" * (2 * size):
            broke = f"offset {size}"
            break
    report.ok(f"a quote riding its own tail still lands ({size} letters)", not broke)


def _pricing(report: Report) -> None:
    report.section("a repeat pays in tokens, never in letters")
    for text in REPEATS:
        tokens = compress(text)
        if len(tokens) >= len(text):
            report.equal(f"{text[:16]!r}... cost letters, not tokens", "break", "none")
            return
    report.ok("every shipped repeat cost strictly fewer tokens than letters", True)
    for text in TEXTS:
        if len(compress(text)) > naive_size(text):
            report.equal(f"{text!r} outbid the naive coder", "break", "none")
            return
    report.ok("no shipped text cost more than the naive coder's price", True)
    report.equal("the naive price is one token per letter", naive_size("abra"), 4)


def _edges(report: Report) -> None:
    report.section("empty texts and single letters answer honestly")
    report.equal("the empty text streams empty", compress(""), [])
    report.equal("the empty stream reads empty", decompress([]), "")
    report.equal("one letter is one literal", compress("a"), [Literal("a")])
    report.equal("two letters never quote themselves", len(compress("ab")), 2)
    report.equal("the audit of nothing is nothing", audit([]), [])
    report.refuses("a loud compress is refused", lambda: compress("ABRA"), TextError)
    report.equal("the oracle prices the empty text", naive_size(""), 0)


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
    report.ok("the report prices every text", len(report_lines(TEXTS)) == len(TEXTS))


def _storms(report: Report) -> None:
    report.section("the storm, loop against loop")
    for seed in (13, 77):
        storm = run_storm(seed=seed)
        report.equal(f"the storm ran its steps (seed {seed})", storm.steps, 140)
        report.equal(f"the storm broke nothing (seed {seed})", storm.breaks, ())
        report.ok(f"the storm held (seed {seed})", storm.seated)
        report.ok(
            f"the storm checked as much as it stepped (seed {seed})",
            storm.checks >= storm.steps,
        )
    report.ok("seeded streams audit silent", honest_streams(24, seed=3))
    report.refuses("a storm without steps is refused", lambda: run_storm(steps=0),
                   WorkloadError)


def _tangles(report: Report) -> None:
    report.section("the tangle: a random walk, closed twice")
    for seed in (5, 31):
        rng = random.Random(seed)
        broke = False
        for _ in range(80):
            stem = "".join(rng.choice("abnra") for _ in range(rng.randint(1, 6)))
            text = stem * rng.randint(1, 8)
            if decompress(compress(text)) != text or audit(compress(text)):
                broke = True
                break
        report.ok(f"eighty tangles closed the loop (seed {seed})", not broke)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import coder as coder_module

    report.ok(
        "the marker the detector looks for is in the coder module",
        FIXTURE in " ".join((coder_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _gate(report)
    _tokens(report)
    _loop(report)
    _honest(report)
    _pricing(report)
    _edges(report)
    _corpora(report)
    _storms(report)
    _tangles(report)
    _stories(report)
    return report
