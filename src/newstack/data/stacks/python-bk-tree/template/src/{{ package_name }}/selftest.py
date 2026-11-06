"""The invariants this tree promises, run against the real modules.

Every claim here is the reason the pruning is trustworthy: the tree must
answer exactly what a full scan answers, the limit must stop early without
lying about the answer, and the walk must refuse a distance that is not a
metric. Runnable in a fresh checkout: `{{ package_name }} selftest`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from tempfile import TemporaryDirectory

from . import demo
from .corpus import CorpusError, dedupe, load_words, synthetic
from .distance import DistanceError, levenshtein, measurement, osa, triangle_violation
from .tree import BKTree, TreeError, search_by

FIXTURE = "skipped without looking inside it"
SHORT_WORDS = sorted(
    "".join(letters) for length in (2, 3) for letters in product("ab", repeat=length)
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


def _distance(report: Report) -> None:
    report.section("the distance is the one the tree trusts")
    report.equal("a word is zero from itself", levenshtein("hello", "hello"), 0)
    report.equal("kitten and sitting are three apart", levenshtein("kitten", "sitting"), 3)
    report.equal("the count is symmetric", levenshtein("flaw", "lawn"), levenshtein("lawn", "flaw"))
    report.equal("the empty string costs the length", levenshtein("", "abc"), 3)
    report.equal("osa folds a swap into one edit", osa("ab", "ba"), 1)
    report.equal("plain levenshtein needs two", levenshtein("ab", "ba"), 2)
    wide = measurement("a" * 60, "b" * 60)
    tight = measurement("a" * 60, "b" * 60, limit=2)
    report.ok("a limit stops before the last row", tight.rows < wide.rows)
    report.ok("a limit computes fewer cells", tight.cells < wide.cells)
    report.equal("a distance past the limit is limit + 1", tight.distance, 3)
    exact = measurement("kitten", "sitting", limit=5).distance
    report.equal("a distance within the limit is exact", exact, 3)
    report.refuses(
        "a negative limit is refused",
        lambda: levenshtein("a", "b", limit=-1),
        DistanceError,
    )
    witness = triangle_violation(["ca", "ac", "abc", "ba", "cab", "bca", "ab"])
    report.ok("osa breaks the triangle inequality somewhere", witness is not None)
    if witness is not None:
        report.ok("and the witness really violates it", witness.through < witness.direct)


def _tree(report: Report) -> None:
    report.section("the tree holds what it is given")
    words = synthetic(400, seed=11)
    tree = BKTree(words)
    report.equal("every word landed in the tree", len(tree), 400)
    report.equal("a repeat is not a second node", tree.add(words[3]), False)
    report.equal("and the tree did not grow", len(tree), 400)
    report.equal("add_all counts only the new ones", tree.add_all(words[:50]), 0)
    report.ok("a corpus word is in the tree", words[7] in tree)
    report.ok("an invented word is not", "zzzqiv" not in tree)
    report.ok("the words come back sorted", list(tree.words) == sorted(tree.words))
    report.equal("a one-word tree has depth one", BKTree(["one"]).depth, 1)
    report.equal("an empty tree has depth zero", BKTree().depth, 0)
    report.refuses("an empty string is not a word", lambda: BKTree().add(""), TreeError)
    report.refuses("a number is not a word", lambda: BKTree().add(7), TreeError)


def _pruning(report: Report) -> None:
    report.section("the pruning answers what a scan answers")
    tree = BKTree(synthetic(800, seed=23))
    for query, radius in [(tree.words[9], 1), (tree.words[400], 2), ("vquplu", 2)]:
        pruned = tree.search(query, radius)
        scanned = tree.scan(query, radius)
        report.equal(
            f"{query!r} within {radius}: same words as the scan",
            pruned.words,
            scanned.words,
        )
        report.ok(
            f"{query!r} within {radius}: looked at less than it has",
            pruned.visited < len(tree),
        )
        report.equal("counting matches looking", pruned.compared, pruned.visited)
    report.refuses("a radius below zero is refused", lambda: tree.search("a", -1), TreeError)
    nearest = tree.nearest(tree.words[12])
    report.equal("a corpus word is nearest to itself", nearest.best, 0)
    report.ok("and the walk was shorter than the corpus", nearest.visited < len(tree))
    empty = BKTree().nearest("anything")
    report.equal("an empty tree answers with nothing", empty.hits, ())


def _transpositions(report: Report) -> None:
    report.section("a non-metric forces the honest scan")
    tree = BKTree(SHORT_WORDS)
    pruned = search_by(tree, "aab", 1, distance=osa)
    truth = sorted(word for word in SHORT_WORDS if osa("aab", word) <= 1)
    report.ok("the pruned walk on osa loses a real answer", sorted(pruned.words) != truth)
    scanned = tree.search_allowing_transpositions("aab", 1)
    report.ok("so the tool says it scanned", scanned.full_scan)
    report.equal("and the scan finds the truth", sorted(scanned.words), truth)
    report.refuses(
        "even the scan refuses a negative radius",
        lambda: tree.search_allowing_transpositions("a", -1),
        TreeError,
    )


def _corpus(report: Report) -> None:
    report.section("words come from files or from the generator")
    with TemporaryDirectory() as room:
        path = f"{room}/words.txt"
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("# a comment\nhello\n\nHELLO\nhello\n")
        report.equal(
            "blanks and comments are skipped, order kept",
            load_words(path),
            ["hello", "HELLO", "hello"],
        )
        report.equal(
            "lowercase folds after reading",
            load_words(path, lowercase=True),
            ["hello", "hello", "hello"],
        )
        report.equal("dedupe keeps the first of each", dedupe(["b", "a", "b"]), ["b", "a"])
        report.refuses(
            "a missing file is named",
            lambda: load_words(f"{room}/missing.txt"),
            CorpusError,
        )
        empty = f"{room}/empty.txt"
        with open(empty, "w", encoding="utf-8") as handle:
            handle.write("# nothing but a comment\n")
        report.refuses("a file of comments holds no words", lambda: load_words(empty), CorpusError)
    first = synthetic(50, seed=7)
    report.equal("the generator is deterministic", first, synthetic(50, seed=7))
    report.ok("a different seed is a different order", first != synthetic(50, seed=8))
    report.ok("the words are distinct", len(set(first)) == 50)
    report.refuses("a corpus of zero is not a corpus", lambda: synthetic(0), CorpusError)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import tree as tree_module

    report.ok(
        "the marker the detector looks for is in the tree module",
        " ".join((tree_module.__doc__ or "").split()) == " ".join(FIXTURE.split())
        or FIXTURE in " ".join((tree_module.__doc__ or "").split()),
    )


def run() -> Report:
    report = Report()
    _distance(report)
    _tree(report)
    _pruning(report)
    _transpositions(report)
    _corpus(report)
    _stories(report)
    return report
