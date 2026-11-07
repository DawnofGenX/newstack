"""The invariants this coder promises, run against the real modules.

Every claim here is the reason the loop can be trusted: the bits
must decode to the letters they were sent, on shipped and seeded
corpora; no shipped code may prefix another; a skewed text must
pay strictly under eight bits a letter; and the tree walk and the
table must agree. Runnable in a fresh checkout: `python -m the-
package selftest`.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
from .coder import (
    CoderError,
    decode,
    encode,
    honest,
    size_report,
)
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_texts,
    report_lines,
    stream_json,
    synthetic,
    write_texts,
)
from .freq import (
    FrequencyError,
    ensure_frequencies,
    tally,
)
from .table import (
    CodeTable,
    TableError,
    audit,
    code_table,
    deal,
)
from .text import LETTERS, MAX_TEXT, TextError, ensure_text
from .tree import (
    Branch,
    Leaf,
    Node,
    TreeError,
    build_tree,
    depths,
    height,
    walk,
    walk_table_agreement,
)
from .workload import WorkloadError, honest_streams, run_storm

FIXTURE = "a decoder never asks for the tree"
TEXTS = (
    "",
    "a",
    "ab",
    "abracadabra",
    "bananabananabana",
    "mississippimississippi",
    "aaaaaaaaaaaaaaaaaaaaaaaa",
    "thequickbrownfoxjumpsoverthelazydog",
)
SKEWED = (
    "aaaaaaaaaabbbbcc",
    "aaaaaaaaaaaaaaaaaaaaaaaa",
    "zzzzzzzzzzzzzzzzyyyyxxxx",
    "eeeeeaaaabbbbccddd",
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


def _weights(report: Report) -> None:
    report.section("the weights are alphabetical and honest")
    report.equal("tally counts", tally("aab"), {"a": 2, "b": 1})
    report.equal("silences are absent", list(tally("ab")), ["a", "b"])
    report.equal("a map comes back itself", ensure_frequencies({"b": 2, "a": 1}), {"a": 1, "b": 2})
    report.refuses("an uppercase weight is refused", lambda: tally("Abra"), TextError)
    report.refuses(
        "a zero weight is refused",
        lambda: ensure_frequencies({"a": 0}),
        FrequencyError,
    )
    report.refuses(
        "a noisy map is refused",
        lambda: ensure_frequencies({"a": -1}),
        FrequencyError,
    )


def _ladder(report: Report) -> Node | None:
    report.section("the ladder takes the two cheapest, ties alphabetical")
    weights = {"a": 1, "b": 1, "c": 5}
    ladder = build_tree(weights)
    report.ok("the ladder weighs the whole text", ladder.weight == 7)
    if not isinstance(ladder, Branch) or not isinstance(ladder.left, Branch):
        report.equal("the lightest pair merged first", "shape", "a-b under c")
        return None
    if not (isinstance(ladder.left.left, Leaf) and isinstance(ladder.left.right, Leaf)):
        report.equal("the first merge is two leaves", "shape", "leaves")
        return None
    report.equal(
        "the first merge is a and b, never c",
        (ladder.left.left.letter, ladder.left.right.letter),
        ("a", "b"),
    )
    report.equal("the ladder is deterministic", build_tree(weights), ladder)
    report.equal(
        "the same weights always build the same ladder",
        build_tree({"b": 1, "a": 1, "c": 5}),
        ladder,
    )
    report.refuses("no tree from no letters", lambda: build_tree({}), TreeError)
    report.refuses("a half tree walks nowhere", lambda: walk(ladder, ""), TreeError)
    report.refuses("noise walks nowhere", lambda: walk(ladder, "2"), TreeError)
    report.equal(
        "the harvest names every letter",
        sorted(depths(ladder)),
        ["a", "b", "c"],
    )
    report.equal("the ladder prices its priciest word", height(ladder), 2)
    return ladder


def _table(report: Report, ladder: Node | None) -> CodeTable | None:
    report.section("the table is canonical, prefix-free, and agrees with the walk")
    if ladder is None:
        report.equal("no ladder means no table to check", "skipped", "skipped")
        return None
    weights = {"a": 1, "b": 1, "c": 5}
    book = code_table(weights)
    report.equal("the heavy letter speaks short", book.bits_for("c"), "0")
    report.equal("the light letters speak long", (book.bits_for("a"), book.bits_for("b")),
                 ("10", "11"))
    report.equal("the table audits silent", audit(book), [])
    report.equal("the ladder and the table agree", walk_table_agreement(ladder, book), True)
    report.equal("reading letters is reading words", book.letter_for("10"), "a")
    report.refuses("a stranger is no word", lambda: book.letter_for("111"), TableError)
    report.refuses("no letters means no table", lambda: code_table({}), TreeError)
    big = code_table(tally("thequickbrownfoxjumpsoverthelazydog"))
    report.equal("a full alphabet table audits silent", audit(big), [])
    report.equal("the deal from a foreign ladder audits silent", audit(deal(ladder)), [])
    return book


def _loop(report: Report) -> None:
    report.section("the bits decode to the letters they were sent")
    for text in TEXTS:
        if not text:
            continue
        book = code_table(tally(text))
        if decode(encode(text, book), book) != text:
            report.equal(f"{text!r} did not survive the loop", "break", "none")
            return
        if audit(book):
            report.equal(f"{text!r} shipped a prefix of another code", "break", "none")
            return
    report.ok("every shipped text closed the loop, audit silent", True)
    corpus = synthetic(40, seed=23)
    for text in corpus:
        book = code_table(tally(text))
        if decode(encode(text, book), book) != text:
            report.equal(f"corpus {text!r} broke the loop", "break", "none")
            return
    report.ok("a seeded corpus closed the loop, text after text", True)
    report.ok("the coder grades its own promise", all(honest(text) for text in TEXTS[1:]))


def _price(report: Report) -> None:
    report.section("a skewed text pays strictly under eight bits a letter")
    for text in SKEWED:
        letters, bits, _ = size_report(text)
        if bits >= letters * 8:
            report.equal(f"{text[:16]!r}... never blinked", "break", "none")
            return
    report.ok("every skewed text paid strictly under eight bits a letter", True)
    flat = code_table({letter: 1 for letter in "abcdefgh"})
    report.ok("eight flat letters price at three bits",
              len(flat.codes) == 8 and all(len(word) == 3 for word in flat.codes.values()))
    letters, bits, _ = size_report("aaaaaaaaaabbbbcc")
    report.ok(f"the skewed ledger priced {bits} bits under {letters * 8}", bits < letters * 8)


def _edges(report: Report) -> None:
    report.section("empty texts and lone letters answer honestly")
    report.equal("the empty text spends no bits", encode(""), "")
    report.equal("no bits read no letters", decode("", code_table({"a": 1})), "")
    report.equal("a lone letter speaks '0'", code_table({"a": 3}).bits_for("a"), "0")
    report.equal("a lone letter loops", decode("0", code_table({"a": 3})), "a")
    report.refuses("a clipped stream is refused",
                   lambda: decode("1", code_table({"a": 1, "b": 2, "c": 3})), CoderError)
    report.refuses("noise bits are refused", lambda: decode("02", code_table({"a": 1})),
                   CoderError)


def _corpora(report: Report) -> None:
    report.section("the corpus in, the ledger out")
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
        report.refuses("a missing corpus is named", lambda: load_texts(f"{room}/missing.txt"),
                       CorpusError)
        noise = f"{room}/noise.txt"
        with open(noise, "w", encoding="utf-8") as handle:
            handle.write("# a comment\n\nAbra\n")
        report.refuses("a noisy corpus is refused", lambda: load_texts(noise), CorpusError)
    report.ok("the ledger prices every text", len(report_lines(list(TEXTS[1:]))) == len(TEXTS) - 1)
    wire = json.loads(stream_json("abracadabra"))
    book = CodeTable(dict(wire["codes"]))
    report.equal("the wire format loops", decode(wire["bits"], book), "abracadabra")


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
    report.ok("seeded tables audit silent", honest_streams(24, seed=3))
    report.refuses("a storm without steps is refused", lambda: run_storm(steps=0),
                   WorkloadError)


def _tangles(report: Report) -> None:
    report.section("the tangle: a random walk, closed twice")
    for seed in (5, 31):
        rng = random.Random(seed)
        broke = False
        for _ in range(80):
            pool = "abnra"[: rng.randint(2, 5)]
            text = "".join(rng.choice(pool) for _ in range(rng.randint(6, 60)))
            book = code_table(tally(text))
            if decode(encode(text, book), book) != text or audit(book):
                broke = True
                break
        report.ok(f"eighty tangles closed the loop (seed {seed})", not broke)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import table as table_module

    report.ok(
        "the marker the detector looks for is in the table module",
        FIXTURE in " ".join((table_module.__doc__ or "").split()).lower(),
    )
    report.ok("the alphabet is the documented one", len(LETTERS) == 26)


def run() -> Report:
    report = Report()
    _gate(report)
    _weights(report)
    ladder = _ladder(report)
    _table(report, ladder)
    _loop(report)
    _price(report)
    _edges(report)
    _corpora(report)
    _storms(report)
    _tangles(report)
    _stories(report)
    return report
