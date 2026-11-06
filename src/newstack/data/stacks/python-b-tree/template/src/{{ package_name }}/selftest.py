"""The invariants this tree promises, run against the real modules.

Every claim here is the reason the balances are trustworthy: the in-order
walk must answer exactly what a sorted list answers, every node below the
root must sit inside the band, every leaf must rest at one level, and the
page file must read back identical after an insert AND delete history.
Runnable in a fresh checkout: `{{ package_name }} selftest`.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory

from .btree import BTree, BTreeError
from .corpus import CorpusError, load_keys, synthetic
from .page import PageError, page_pair

FIXTURE = "never goes jagged"


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


def _balanced(tree: BTree) -> bool:
    """The promise a caller cannot see through: band, ceiling, one leaf level."""
    shapes = tree.shape()
    band = all(shape.keys >= tree.min_keys for shape in shapes if shape.depth > 0)
    ceil = all(shape.keys <= tree.max_keys for shape in shapes)
    flat = tree.leaf_levels <= 1
    return band and ceil and flat


def _band(report: Report) -> None:
    report.section("the band is the order, not a suggestion")
    for order in (2, 3, 5, 13):
        tree = BTree(order, synthetic(60, seed=order))
        report.equal(f"order {order} keeps every node above the floor", _balanced(tree), True)
        report.equal(f"order {order} walks to a sorted corpus", tree.keys, sorted(set(tree.keys)))
    report.refuses("order one is refused", lambda: BTree(1), BTreeError)
    report.refuses(
        "a fractional order is refused",
        lambda: BTree(2.5),  # type: ignore[arg-type]
        BTreeError,
    )


def _insertion(report: Report) -> None:
    report.section("insertion splits on the way down")
    tree = BTree(2)
    for key in range(3):
        report.ok(f"the fresh {key} is accepted", tree.insert(key))
    report.equal("a duplicate costs nothing", tree.insert(1), False)
    flood = BTree(3, range(64))
    report.equal("a flooded tree walks to the flood", flood.keys, list(range(64)))
    report.ok("and never goes over the ceiling", all(s.keys <= 5 for s in flood.shape()))
    report.equal("a repeated key is not a second key", len(BTree(3, [7, 7, 7])), 1)


def _deletion(report: Report) -> None:
    report.section("deletion borrows before it merges")
    tree = BTree(3, range(48))
    for key in range(0, 48, 2):
        report.ok(f"the even {key} leaves", tree.delete(key))
    report.equal("the odd keys remain, in order", tree.keys, list(range(1, 48, 2)))
    report.ok("and the tree stays balanced", _balanced(tree))
    report.ok("a vanished key stays gone", not tree.delete(4))
    while tree.keys:
        tree.delete(tree.keys[0])
    report.equal("a drained tree is empty", len(tree), 0)
    report.equal("an empty tree has no leaf levels", tree.leaf_levels, 0)
    report.equal("and zero height", tree.height, 0)


def _random_ops(report: Report) -> None:
    report.section("a seeded op-mix matches a sorted list, always")
    for order in (2, 3, 5):
        for seed in (11, 29):
            rng = random.Random(seed * 31 + order)
            tree = BTree(order)
            shelf: list[int] = []
            for _ in range(300):
                key = rng.randrange(-400, 400)
                if rng.random() < 0.55:
                    present = key in shelf
                    landed = tree.insert(key)
                    if landed:
                        shelf.append(key)
                    report.ok("the tree and the shelf land together", landed is not present)
                else:
                    present = key in shelf
                    gone = tree.delete(key)
                    if gone:
                        shelf.remove(key)
                    report.ok("the tree and the shelf forget together", gone is present)
                if len(shelf) % 37 == 0 and shelf:
                    report.equal("the walk is the shelf", tree.keys, sorted(shelf))
            report.equal(f"order {order} seed {seed} ends as the shelf", tree.keys, sorted(shelf))
            report.ok(f"order {order} seed {seed} stays balanced", _balanced(tree))


def _window(report: Report) -> None:
    report.section("the window answers what bisect answers")
    from bisect import bisect_left, bisect_right

    corpus = synthetic(200, seed=7, low=-500, high=500)
    tree = BTree(4, corpus)
    shelf = sorted(corpus)
    for low, high in ((-500, 500), (-13, 91), (77, 77), (250, -250 + 500)):
        if low <= high:
            report.equal(
                f"window [{low}..{high}]",
                tree.range_scan(low, high),
                shelf[bisect_left(shelf, low) : bisect_right(shelf, high)],
            )
    report.refuses("an inverted window is refused", lambda: tree.range_scan(9, 3), BTreeError)


def _page(report: Report) -> None:
    report.section("the page file reads back identical")
    with TemporaryDirectory() as room:
        for order in (2, 3, 5):
            rng = random.Random(order * 7)
            tree = BTree(order)
            for _ in range(150):
                key = rng.randrange(-300, 300)
                if rng.random() < 0.5:
                    tree.insert(key)
                else:
                    tree.delete(key)
            path = f"{room}/tree-{order}.page"
            report.equal(
                f"order {order} survives the freeze", page_pair(tree, path).identical, True
            )
            first = Path(path).read_bytes()
            from .page import write_page

            write_page(tree, path)
            report.ok("a rewrite is byte-identical", Path(path).read_bytes() == first)
        bad = Path(room) / "junk.page"
        bad.write_bytes(b"NOTAPAGE" + bytes(40))
        report.refuses("junk is refused by name", lambda: _read(bad), PageError)
        report.refuses("a missing page is named", lambda: _read(f"{room}/gone.page"), PageError)


def _read(path: str) -> object:
    from .page import read_page

    return read_page(path)


def _corpus(report: Report) -> None:
    report.section("keys come from files or from the generator")
    with TemporaryDirectory() as room:
        path = f"{room}/keys.txt"
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("# a comment\n7\n\n-3\n7\n")
        report.equal(
            "blanks and comments are skipped, order kept",
            load_keys(path),
            [7, -3, 7],
        )
        empty = f"{room}/empty.txt"
        with open(empty, "w", encoding="utf-8") as handle:
            handle.write("# nothing but a comment\n")
        report.refuses("a file of comments holds no keys", lambda: load_keys(empty), CorpusError)
        junk = f"{room}/junk.txt"
        with open(junk, "w", encoding="utf-8") as handle:
            handle.write("seven\n")
        report.refuses("a non-integer line is named", lambda: load_keys(junk), CorpusError)
    first = synthetic(50, seed=7)
    report.equal("the generator is deterministic", first, synthetic(50, seed=7))
    report.ok("a different seed is a different order", first != synthetic(50, seed=8))
    report.ok("the keys are distinct", len(set(first)) == 50)
    report.refuses("a corpus of zero is not a corpus", lambda: synthetic(0), CorpusError)
    report.refuses("an empty span is refused", lambda: synthetic(4, low=5, high=5), CorpusError)


def _marker(report: Report) -> None:
    report.section("the phrase the detector looks for ships in the code")
    from . import btree as btree_module

    joined = " ".join((btree_module.__doc__ or "").split())
    report.ok("the marker sits in the tree module docstring", FIXTURE in joined)


def run() -> Report:
    report = Report()
    _band(report)
    _insertion(report)
    _deletion(report)
    _random_ops(report)
    _window(report)
    _page(report)
    _corpus(report)
    _marker(report)
    return report
