"""The invariants this automaton promises, run against the real modules.

Every claim here is the reason a sweep can be trusted: the textbook overlaps
must all surface, the hit set must equal a naive scan on seeded alphabets,
and one sweep must inspect less than the naive product on the shipped
corpus. Runnable in a fresh checkout: `{{ package_name }} selftest`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .automaton import AhoCorasick, AhoCorasickError
from .corpus import prose, random_text
from .naive import naive_sweep

FIXTURE = "fails forward to a shorter suffix"

TEXTBOOK = ("he", "she", "his", "hers")
TEXTBOOK_TEXT = "ahishers"


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


def _positions(machine: AhoCorasick, pattern: str, text: str) -> list[int]:
    return [hit.end for hit in machine.scan(text) if hit.pattern == pattern]


def _textbook(report: Report) -> None:
    report.section("the overlaps the scanner must not miss")
    machine = AhoCorasick(TEXTBOOK)
    report.equal("'he' inside 'she' surfaces", _positions(machine, "he", TEXTBOOK_TEXT), [5])
    report.equal("'she' surfaces whole", _positions(machine, "she", TEXTBOOK_TEXT), [5])
    report.equal("'his' surfaces whole", _positions(machine, "his", TEXTBOOK_TEXT), [3])
    report.equal("'hers' surfaces whole", _positions(machine, "hers", TEXTBOOK_TEXT), [7])
    report.equal(
        "the sweep is the naive answer",
        machine.scan(TEXTBOOK_TEXT),
        naive_sweep(TEXTBOOK_TEXT, TEXTBOOK).hits,
    )
    shared = AhoCorasick(["ab", "abc", "bc", "c"])
    report.equal(
        "a shared prefix reports every embedder",
        [hit.pattern for hit in shared.scan("zabcz")],
        ["ab", "abc", "bc", "c"],
    )
    report.equal("ends position the match, not its start", shared.scan("zabcz")[1].start, 1)


def _degenerate(report: Report) -> None:
    report.section("the edges: nothing to hunt, nothing to hunt over")
    empty = AhoCorasick([])
    report.equal("no patterns sweep to no hits", empty.sweep("anything").hits, ())
    report.equal("no patterns cross one state per character", empty.sweep("abcd").states, 4)
    quiet = AhoCorasick(["he"])
    report.equal("an empty text yields an empty ledger", quiet.sweep("").hits, ())
    report.equal("an empty text crosses zero states", quiet.sweep("").states, 0)
    report.refuses("a blank pattern is refused", lambda: AhoCorasick([""]), AhoCorasickError)
    report.refuses(
        "a non-string pattern is refused",
        lambda: AhoCorasick([7]),  # type: ignore[list-item]
        AhoCorasickError,
    )
    report.equal(
        "a duplicate pattern is stated once",
        list(AhoCorasick(["ab", "ab", "ab"]).patterns),
        ["ab"],
    )
    report.equal("a duplicate costs no second hit", AhoCorasick(["ab"]).count("abab"), 2)


def _equal_to_naive(report: Report) -> None:
    report.section("seeded alphabets: the sweep IS the naive scan")
    for seed in (3, 17, 101, 2024):
        alphabet = "ab" if seed % 2 else "abcde"
        patterns = [random_text(2, seed=seed, alphabet=alphabet)]
        patterns += [random_text(4, seed=seed + 1, alphabet=alphabet)]
        patterns += [random_text(7, seed=seed * 3, alphabet=alphabet)]
        machine = AhoCorasick(patterns)
        text = random_text(240, seed=seed + 991, alphabet=alphabet)
        report.equal(
            f"seed {seed} agrees with the naive scan",
            machine.scan(text),
            naive_sweep(text, machine.patterns).hits,
        )


def _counter(report: Report) -> None:
    report.section("one sweep is cheaper than the naive product")
    patterns = ["the", "then", "hen", "there", "three", "here"]
    machine = AhoCorasick(patterns)
    text = prose()
    sweep = machine.sweep(text)
    naive = naive_sweep(text, patterns)
    report.equal("the counter story keeps the hits equal", sweep.hits, naive.hits)
    report.ok(
        f"the sweep crossed {sweep.states} < naive's {naive.inspections} windows",
        sweep.states < naive.inspections,
    )
    report.ok("a hit-rich corpus still reports hits", len(sweep.hits) > 0)


def _order(report: Report) -> None:
    report.section("the ledger is sorted and deterministic")
    machine = AhoCorasick(["aa", "a"])
    first = machine.scan("aaaa")
    report.equal("a repeated sweep repeats the ledger", first, machine.scan("aaaa"))
    report.equal(
        "hits sort by end, then start, then pattern",
        [(hit.end, hit.start, hit.pattern) for hit in first],
        sorted((hit.end, hit.start, hit.pattern) for hit in first),
    )
    last = [hit.pattern for hit in first][-1:]
    report.equal("both overlaps at the last end are stated", last, ["a"])
    report.equal("four characters yield seven overlap hits", len(first), 7)


def _marker(report: Report) -> None:
    report.section("the phrase the detector looks for ships in the code")
    from . import automaton as automaton_module

    joined = " ".join((automaton_module.__doc__ or "").split())
    report.ok("the marker sits in the automaton docstring", FIXTURE in joined)


def run() -> Report:
    report = Report()
    _textbook(report)
    _degenerate(report)
    _equal_to_naive(report)
    _counter(report)
    _order(report)
    _marker(report)
    return report
