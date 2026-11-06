"""Six stories about searching by distance, told with real numbers.

Nothing here is a picture of the algorithm; every claim is a comparison the
demo computes, and `stories` reports whether all of them held.
"""

from __future__ import annotations

from itertools import product

from .corpus import synthetic
from .distance import levenshtein, measurement, osa, triangle_violation
from .tree import BKTree, search_by

__all__ = ["Story", "render_stories", "stories"]

DEMO_CORPUS = 3000
DEMO_SEED = 7


def _short_words(alphabet: str, lengths: tuple[int, ...]) -> list[str]:
    """Every word over `alphabet` at each length in `lengths`, sorted."""
    return sorted(
        "".join(letters) for length in lengths for letters in product(alphabet, repeat=length)
    )


class Story:
    """One story: a claim, the lines that argue for it, and the checks that hold it up."""

    def __init__(self, title: str) -> None:
        self.title = title
        self.lines: list[str] = []
        self.checks: list[tuple[str, bool]] = []

    def say(self, text: str) -> None:
        self.lines.append(f"  {text}")

    def block(self, lines: list[str]) -> None:
        for line in lines:
            self.lines.append(f"  {line}")

    def require(self, claim: str, held: bool) -> None:
        self.checks.append((claim, bool(held)))
        mark = "ok  " if held else "FAIL"
        self.lines.append(f"  {mark} {claim}")

    @property
    def held(self) -> bool:
        return all(held for _, held in self.checks) and bool(self.checks)

    def render(self) -> list[str]:
        return [f"{self.title}", *self.lines]


def _story_distance() -> Story:
    story = Story("1. the distance counts edits, and it is symmetric")
    pairs = [("kitten", "sitting"), ("flaw", "lawn"), ("", "abc")]
    for left, right in pairs:
        forward = levenshtein(left, right)
        backward = levenshtein(right, left)
        story.say(f"{left!r} -> {right!r}: {forward} edit(s), and {backward} the other way")
        story.require(f"{left!r} and {right!r} cost the same both ways", forward == backward)
    story.require("a word is distance zero from itself", levenshtein("hello", "hello") == 0)
    story.require(
        "distance zero happens only between equal words",
        levenshtein("hello", "hellp") == 1,
    )
    return story


def _story_limit() -> Story:
    story = Story("2. a limit stops the walk early")
    left = "a" * 60
    right = "b" * 60
    whole = measurement(left, right)
    bounded = measurement(left, right, limit=2)
    story.say("Two 60-character strings with not one character in common:")
    story.block([f"whole      {whole.line()}", f"limit 2    {bounded.line()}"])
    story.require("the unlimited walk filled every row", whole.rows == len(left))
    story.require("the limited walk stopped before the last row", bounded.rows < whole.rows)
    story.require("the limited walk computed fewer cells", bounded.cells < whole.cells // 2)
    story.require("a distance past the limit is reported as limit + 1", bounded.distance == 3)
    story.require(
        "the distance below the limit is the exact one",
        measurement("kitten", "sitting", limit=5).distance == 3,
    )
    return story


def _story_pruning() -> Story:
    story = Story("3. the tree looks at a fraction of the corpus")
    corpus = synthetic(DEMO_CORPUS, seed=DEMO_SEED)
    tree = BKTree(corpus)
    query = corpus[151]
    radius = 1
    pruned = tree.search(query, radius)
    scanned = tree.scan(query, radius)
    story.say(f"{len(tree)} words, a query of {query!r} within {radius}:")
    story.block(
        [
            f"tree       {pruned.visited} node(s) visited, {pruned.compared} distance(s) computed",
            f"scan       {scanned.visited} word(s) compared,"
            f" {scanned.compared} distance(s) computed",
            f"answers    {len(pruned.hits)} from the tree, {len(scanned.hits)} from the scan",
        ]
    )
    story.require("the tree answered the same words as the scan", pruned.words == scanned.words)
    story.require(
        "the tree computed fewer distances than there are words",
        pruned.compared < len(tree),
    )
    story.require(
        "the tree looked at less than a fortieth of the corpus",
        pruned.visited * 40 < len(tree),
    )
    return story


def _story_order() -> Story:
    story = Story("4. the order of insertion changes the shape, not the answers")
    corpus = synthetic(600, seed=11)
    forward = BKTree(corpus)
    backward = BKTree(list(reversed(corpus)))
    query = corpus[77]
    radius = 2
    left = forward.search(query, radius)
    right = backward.search(query, radius)
    story.say(f"the same {len(corpus)} words, inserted in two orders:")
    story.block(
        [
            f"forwards   depth {forward.depth}, {left.visited} node(s) visited",
            f"reversed   depth {backward.depth}, {right.visited} node(s) visited",
        ]
    )
    story.require("both trees hold every word", len(forward) == len(backward) == len(corpus))
    story.require("both trees answer the same words", left.words == right.words)
    story.require(
        "but the two shapes are not the same walk",
        forward.depth != backward.depth or left.visited != right.visited,
    )
    return story


def _story_metric() -> Story:
    story = Story("5. transpositions are not a metric, so the tree must not prune")
    witness = triangle_violation(["ca", "ac", "abc", "ba", "cab", "bca", "ab"])
    if witness is None:
        story.require("a triangle violation exists for optimal string alignment", False)
        return story
    story.say("Optimal string alignment counts an adjacent swap as one edit, and it breaks")
    story.say("the triangle inequality:")
    story.block(witness.lines())

    # The tree was built by plain edit distance; walking it with OSA prunes on
    # an inequality that no longer holds. Twelve short words over two letters
    # are enough to show an answer going missing, every time, on every machine.
    corpus = _short_words("ab", (2, 3))
    tree = BKTree(corpus)
    query = "aab"
    radius = 1
    pruned = search_by(tree, query, radius, distance=osa)
    truth = sorted(word for word in corpus if osa(query, word) <= radius)
    lost = sorted(set(truth) - set(pruned.words))
    story.say("")
    story.say(f"a pruned walk with OSA, query {query!r} within {radius}:")
    story.block(
        [
            f"pruned     {pruned.words}",
            f"the truth  {tuple(truth)}",
            f"lost       {lost}",
        ]
    )
    story.require("the pruned walk loses a real answer", bool(lost))
    scanned = tree.search_allowing_transpositions(query, radius)
    story.require("so this tool scans when transpositions are on", scanned.full_scan)
    story.require("and the scan finds every word the truth holds", sorted(scanned.words) == truth)
    return story


def _story_identity() -> Story:
    story = Story("6. an exact word is a short walk, and a repeat is not a second node")
    corpus = synthetic(800, seed=5)
    tree = BKTree(corpus)
    story.require("every word is in the tree once", len(tree) == len(corpus))
    story.require("inserting a word twice does not grow the tree", tree.add(corpus[10]) is False)
    story.require("the tree still holds the same number of words", len(tree) == len(corpus))
    exact = tree.nearest(corpus[10])
    story.say(f"nearest to {corpus[10]!r}: {exact.words} at distance {exact.best}")
    story.require("a word in the corpus is at distance zero from itself", exact.best == 0)
    story.require(
        "finding it visited fewer nodes than the corpus has",
        exact.visited < len(tree),
    )
    story.require(
        "and it never computed more distances than it visited",
        exact.compared == exact.visited,
    )
    return story


def stories() -> list[Story]:
    return [
        _story_distance(),
        _story_limit(),
        _story_pruning(),
        _story_order(),
        _story_metric(),
        _story_identity(),
    ]


def render_stories() -> str:
    told = stories()
    lines: list[str] = []
    for story in told:
        lines.extend(story.render())
        lines.append("")
    held = sum(1 for story in told if story.held)
    if held == len(told):
        lines.append(f"stories      {held} of {len(told)} hold")
    else:
        lines.append(f"stories      BROKEN: {held} of {len(told)} hold")
    return "\n".join(lines)
