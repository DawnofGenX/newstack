"""The invariants this trie promises, run against the real modules.

Every claim here is the reason the branches can be trusted: membership
must equal a set's answer on seeded corpora, every prefix listing must
equal the sorted scan, a delete must close exactly one node and leave
survivors seated, and a rebuild from the word list must reproduce every
answer. Runnable in a fresh checkout: `{{ package_name }} selftest`.
"""

from __future__ import annotations

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
from .scan import scan_lcp, scan_prefix
from .trie import PrefixTrie
from .words import WordError, ensure_prefix, ensure_word
from .workload import WorkloadError, rebuild_matches, run_storm

FIXTURE = "a word ends where it is whole"
WORDS = ["car", "cart", "cartwheel", "cat", "catch", "dog", "dogma", "do"]


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
    report.section("the gate keeps letters out of the branches")
    report.equal("a word comes back itself", ensure_word("cart"), "cart")
    report.equal("the empty stem asks for everything", ensure_prefix(""), "")
    report.refuses("the empty string is no word", lambda: ensure_word(""), WordError)
    report.refuses("uppercase has no branch", lambda: ensure_word("Cart"), WordError)
    report.refuses("a digit has no branch", lambda: ensure_word("car1"), WordError)
    report.refuses("a list has no letters", lambda: ensure_word(["car"]), WordError)
    report.refuses(
        "sixty-five letters are past the gate",
        lambda: ensure_word("a" * 65),
        WordError,
    )


def _membership(report: Report) -> None:
    report.section("membership answers what a set answers")
    corpus = synthetic(120, seed=17)
    trie = PrefixTrie(corpus)
    stored = set(corpus)
    report.equal("the count is the set's size", trie.count(), len(stored))
    for word in [*corpus[::11], "zzzzzz", "q", "a"]:
        report.ok(f"{word!r} answers like the set", trie.has(word) == (word in stored))
    report.equal("the walk is the sorted set", trie.walk(), sorted(stored))


def _prefixes(report: Report) -> None:
    report.section("every prefix listing is the sorted scan")
    corpus = synthetic(150, seed=23)
    trie = PrefixTrie(corpus)
    stems = ["", "a", "ab", "co", "z", "qu", corpus[7][:3]]
    for stem in stems:
        report.equal(
            f"stem {stem!r} lists the scan", trie.prefix(stem), scan_prefix(corpus, stem)
        )
    whole = trie.prefix("")
    report.equal("the empty prefix lists every word once", whole, sorted(set(corpus)))
    report.equal("the empty prefix invents nothing", len(whole), len(set(corpus)))


def _deletion(report: Report) -> None:
    report.section("delete closes one node, survivors keep their stems")
    for seed in (7, 41, 1009):
        corpus = synthetic(90, seed=seed)
        trie = PrefixTrie(corpus)
        victim = corpus[seed % len(corpus)]
        stem = victim[:2]
        before = trie.prefix(stem)
        report.ok(f"the victim was a word (seed {seed})", trie.has(victim))
        report.ok(f"the delete lands (seed {seed})", trie.delete(victim))
        report.ok(f"the victim is gone (seed {seed})", not trie.has(victim))
        report.equal(
            f"survivors keep the stem (seed {seed})",
            trie.prefix(stem),
            [word for word in before if word != victim],
        )
        report.ok(f"the trie is seated (seed {seed})", trie.invariant())
        report.ok(f"a second delete finds nothing (seed {seed})", not trie.delete(victim))
        report.equal(f"the count fell by one (seed {seed})", trie.count(), len(corpus) - 1)


def _rebuild(report: Report) -> None:
    report.section("a rebuild reproduces every answer")
    corpus = synthetic(80, seed=55)
    report.ok("two tries, one corpus, identical answers", rebuild_matches(corpus))
    first = PrefixTrie(corpus)
    second = PrefixTrie(list(reversed(corpus)))
    report.equal("insertion order is not an answer", first.walk(), second.walk())
    report.equal(
        "the rebuilt listing equals the first", first.prefix("a"), second.prefix("a")
    )


def _shared(report: Report) -> None:
    report.section("the common stem belongs to every word")
    trie = PrefixTrie(["cart", "car", "cartwheel"])
    report.equal("car is the stem of the cart family", trie.longest_common_prefix(), "car")
    report.equal("the scan agrees", scan_lcp(["cart", "car", "cartwheel"]), "car")
    report.equal("strangers share nothing", PrefixTrie(["car", "dog"]).longest_common_prefix(), "")
    report.equal("one word shares itself", PrefixTrie(["solo"]).longest_common_prefix(), "solo")
    report.equal("no words share nothing", PrefixTrie().longest_common_prefix(), "")


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
    report.section("the storm, re-checked after every op")
    for seed in (13, 77):
        storm = run_storm(seed=seed)
        report.equal(f"the storm ran its steps (seed {seed})", storm.steps, 160)
        report.equal(f"the storm broke nothing (seed {seed})", storm.breaks, 0)
        report.ok(f"the storm stayed seated (seed {seed})", storm.ordered)
        report.ok(f"the storm checked more than it stepped (seed {seed})",
                  storm.checks > storm.steps)
    report.refuses(
        "a storm without steps is refused", lambda: run_storm(steps=0), WorkloadError
    )


def _empty(report: Report) -> None:
    report.section("an empty trie answers without complaint")
    bare = PrefixTrie()
    report.equal("the walk of nothing", bare.walk(), [])
    report.equal("a stem of nothing", bare.prefix("a"), [])
    report.equal("nothing is held", bare.count(), 0)
    report.ok("nothing is seated", bare.invariant())
    report.ok("nothing answers membership", not bare.has("car"))
    report.ok("nothing is deleted", not bare.delete("car"))


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import trie as trie_module

    report.ok(
        "the marker the detector looks for is in the trie module",
        FIXTURE in " ".join((trie_module.__doc__ or "").split()),
    )


def run() -> Report:
    report = Report()
    _gate(report)
    _membership(report)
    _prefixes(report)
    _deletion(report)
    _rebuild(report)
    _shared(report)
    _corpora(report)
    _storms(report)
    _empty(report)
    _stories(report)
    return report
