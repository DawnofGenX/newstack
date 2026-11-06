"""A Burkhard-Keller tree: words arranged by the distance between them.

Every node holds one word and one child per distinct distance to that word. To
find words within distance N of a query, walk to a node, measure the query
against the node's word, and step into only the children whose edge distance
lies in [d - N, d + N] — because the distance is a metric, so a node can be
skipped without looking inside it.

That is the whole trick, and it is only a trick when the distance really is a
metric. Adjacent transpositions make it not a metric, so a tree search with
transpositions is not pruned here: it scans, and says so.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from .distance import levenshtein, osa

__all__ = ["BKTree", "Hit", "Search", "TreeError", "search_by"]


class TreeError(ValueError):
    """The tree was asked for something it cannot do."""


@dataclass(frozen=True)
class Hit:
    word: str
    distance: int

    def line(self) -> str:
        return f"  {self.distance}  {self.word}"


@dataclass(frozen=True)
class Search:
    """What one search did, and how much of the corpus it had to look at."""

    query: str
    max_distance: int
    hits: tuple[Hit, ...]
    visited: int
    compared: int
    corpus: int
    full_scan: bool = False

    @property
    def words(self) -> tuple[str, ...]:
        return tuple(hit.word for hit in self.hits)

    @property
    def best(self) -> int | None:
        return min((hit.distance for hit in self.hits), default=None)

    @property
    def pruned(self) -> int:
        return self.corpus - self.visited

    def lines(self) -> list[str]:
        mode = "full scan" if self.full_scan else "pruned by the triangle inequality"
        return [
            f"query      {self.query!r} within {self.max_distance}",
            f"corpus     {self.corpus} word(s)",
            f"looked at  {self.visited} node(s), {self.compared} distance(s) computed ({mode})",
            f"found      {len(self.hits)} word(s)",
            *[hit.line() for hit in self.hits],
        ]


@dataclass
class _Node:
    word: str
    children: dict[int, _Node] = field(default_factory=dict)


class BKTree:
    """Words in a tree whose edges are distances."""

    def __init__(self, words: list[str] | tuple[str, ...] = ()) -> None:
        self._root: _Node | None = None
        self._size = 0
        self._depth = 0
        for word in words:
            self.add(word)

    def __len__(self) -> int:
        return self._size

    def __contains__(self, word: object) -> bool:
        if not isinstance(word, str):
            return False
        return bool(self.search(word, 0).hits)

    @property
    def depth(self) -> int:
        """The number of nodes on the longest path from the root to a leaf."""
        self._depth = 0

        def walk(node: _Node, level: int) -> None:
            self._depth = max(self._depth, level)
            for child in node.children.values():
                walk(child, level + 1)

        if self._root is not None:
            walk(self._root, 1)
        return self._depth

    @property
    def words(self) -> tuple[str, ...]:
        found: list[str] = []

        def walk(node: _Node) -> None:
            found.append(node.word)
            for child in node.children.values():
                walk(child)

        if self._root is not None:
            walk(self._root)
        return tuple(sorted(found))

    def add(self, word: str) -> bool:
        """Insert a word. Returns False when it was already there."""
        if not isinstance(word, str):
            raise TreeError(f"a tree holds strings, not {type(word).__name__}")
        if not word:
            raise TreeError("an empty string is not a word; it is distance 1 from everything")
        if self._root is None:
            self._root = _Node(word)
            self._size = 1
            return True
        node = self._root
        while True:
            gap = levenshtein(word, node.word)
            if gap == 0:
                return False
            child = node.children.get(gap)
            if child is None:
                node.children[gap] = _Node(word)
                self._size += 1
                return True
            node = child

    def add_all(self, words: list[str] | tuple[str, ...]) -> int:
        return sum(1 for word in words if self.add(word))

    def search(self, word: str, max_distance: int) -> Search:
        """Every word within max_distance of the query, pruned where it is safe."""
        return search_by(self, word, max_distance, distance=levenshtein)

    def search_allowing_transpositions(self, word: str, max_distance: int) -> Search:
        """The same search with OSA distance, which is not a metric: so it scans."""
        if max_distance < 0:
            raise TreeError("a search radius below zero reaches nothing, not even the query")
        hits: list[Hit] = []
        for candidate in self.words:
            gap = osa(word, candidate)
            if gap <= max_distance:
                hits.append(Hit(candidate, gap))
        hits.sort(key=lambda hit: (hit.distance, hit.word))
        compared = len(self.words)
        return Search(
            word, max_distance, tuple(hits), compared, compared, self._size, full_scan=True
        )

    def scan(self, word: str, max_distance: int) -> Search:
        """The honest comparison: measure the query against every word."""
        hits = [
            Hit(candidate, levenshtein(word, candidate))
            for candidate in self.words
            if levenshtein(word, candidate) <= max_distance
        ]
        hits.sort(key=lambda hit: (hit.distance, hit.word))
        compared = len(self.words)
        return Search(
            word, max_distance, tuple(hits), compared, compared, self._size, full_scan=True
        )

    def nearest(self, word: str) -> Search:
        """The closest words, found by tightening the radius as the walk descends."""
        if self._root is None:
            return Search(word, 0, (), 0, 0, 0)
        best: int | None = None
        hits: list[str] = []
        visited = 0
        compared = 0
        stack = [self._root]
        while stack:
            node = stack.pop()
            visited += 1
            gap = levenshtein(word, node.word)
            compared += 1
            if best is None or gap < best:
                best = gap
                hits = [node.word]
            elif gap == best:
                hits.append(node.word)
            if best == 0:
                continue
            for edge, child in node.children.items():
                if best is None or abs(gap - edge) <= best:
                    stack.append(child)
        distance = 0 if best is None else best
        found = tuple(Hit(name, distance) for name in sorted(hits))
        return Search(word, distance, found, visited, compared, self._size)


def search_by(
    tree: BKTree,
    word: str,
    max_distance: int,
    *,
    distance: Callable[[str, str], int] = levenshtein,
) -> Search:
    """A pruned walk with whatever distance the caller hands it.

    The walk trusts that `distance` is a metric. Hand it the OSA variant and it
    will prune away real answers, which is exactly what the demo shows.
    """
    if max_distance < 0:
        raise TreeError("a search radius below zero reaches nothing, not even the query")
    root = tree._root
    if root is None:
        return Search(word, max_distance, (), 0, 0, 0)
    measure = distance
    hits: list[Hit] = []
    visited = 0
    compared = 0
    stack = [root]
    while stack:
        node = stack.pop()
        visited += 1
        gap = measure(word, node.word)
        compared += 1
        if gap <= max_distance:
            hits.append(Hit(node.word, gap))
        low = gap - max_distance
        high = gap + max_distance
        for edge, child in node.children.items():
            if low <= edge <= high:
                stack.append(child)
    hits.sort(key=lambda hit: (hit.distance, hit.word))
    return Search(word, max_distance, tuple(hits), visited, compared, len(tree))
