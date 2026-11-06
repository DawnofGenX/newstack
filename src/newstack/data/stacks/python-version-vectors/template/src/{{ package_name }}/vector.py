"""A version vector is one counter per writer, and a partial order over them.

The point of the vector is not that it orders events - it is that it refuses to order
two events it cannot compare: a total order can be different on two replicas, while a
comparison of vectors gives one verdict everywhere, and that verdict is sometimes
"concurrent".
"""

from __future__ import annotations

from enum import StrEnum

SEPARATOR = ":"
LIST_SEPARATOR = ","
"""The text form is ``a:2,b:1``: a name, a colon, a count, sorted by name."""


class VectorError(ValueError):
    """A vector that cannot be built, parsed, or compared as asked."""


class Relation(StrEnum):
    """The four answers a comparison can give."""

    EQUAL = "equal"
    BEFORE = "before"
    AFTER = "after"
    CONCURRENT = "concurrent"


def _check_node(node: str) -> str:
    if not isinstance(node, str):
        raise VectorError(f"a node name is a string, not {type(node).__name__}")
    if not node:
        raise VectorError("a node name cannot be empty")
    if SEPARATOR in node or LIST_SEPARATOR in node:
        raise VectorError(
            f"a node name cannot contain {SEPARATOR!r} or {LIST_SEPARATOR!r}: {node!r}"
        )
    return node


def _check_count(count: int) -> int:
    if isinstance(count, bool) or not isinstance(count, int):
        raise VectorError(f"a counter is a whole number, not {count!r}")
    if count < 0:
        raise VectorError(f"a counter cannot be negative: {count}")
    return count


class VersionVector:
    """One counter per writer. Instances are treated as immutable.

    Every operation returns a new vector, because a merge that mutated its argument
    would make the order of merges matter, and the order of merges is exactly what a
    vector is supposed to make irrelevant.
    """

    __slots__ = ("_counts",)

    def __init__(self, counts: dict[str, int] | None = None) -> None:
        clean: dict[str, int] = {}
        for node, count in (counts or {}).items():
            clean[_check_node(node)] = _check_count(count)
        self._counts = clean

    @classmethod
    def empty(cls) -> VersionVector:
        return cls({})

    @classmethod
    def parse(cls, text: str) -> VersionVector:
        """Read the ``a:2,b:1`` form. An empty string is the empty vector."""
        if not isinstance(text, str):
            raise VectorError(f"a vector is read from text, not {type(text).__name__}")
        if not text.strip():
            return cls.empty()
        counts: dict[str, int] = {}
        for chunk in text.split(LIST_SEPARATOR):
            piece = chunk.strip()
            if not piece:
                raise VectorError(f"empty entry in {text!r}")
            if SEPARATOR not in piece:
                raise VectorError(f"{piece!r} has no {SEPARATOR!r}: the form is name:count")
            node, _, number = piece.partition(SEPARATOR)
            node = _check_node(node.strip())
            if node in counts:
                raise VectorError(f"{node!r} appears twice in {text!r}")
            try:
                counts[node] = _check_count(int(number))
            except ValueError as error:
                raise VectorError(f"{number!r} is not a whole number") from error
        return cls(counts)

    def counts(self) -> dict[str, int]:
        """A copy, so a caller cannot reach in and change the vector."""
        return dict(self._counts)

    def nodes(self) -> tuple[str, ...]:
        return tuple(sorted(self._counts))

    def get(self, node: str) -> int:
        return self._counts.get(node, 0)

    def total(self) -> int:
        return sum(self._counts.values())

    def increment(self, node: str) -> VersionVector:
        """The next event by `node`: everyone else's counters are unchanged."""
        _check_node(node)
        counts = dict(self._counts)
        counts[node] = counts.get(node, 0) + 1
        return VersionVector(counts)

    def merge(self, other: VersionVector) -> VersionVector:
        """The join: pointwise maximum. Order, repetition and place do not matter."""
        merged = dict(self._counts)
        for node, count in other._counts.items():
            if count > merged.get(node, 0):
                merged[node] = count
        return VersionVector(merged)

    def dominates(self, other: VersionVector) -> bool:
        """True when every counter here is at least the other's (i.e. `other <= self`)."""
        return all(self.get(node) >= count for node, count in other._counts.items())

    def compare(self, other: VersionVector) -> Relation:
        """EQUAL, BEFORE, AFTER, or CONCURRENT - never a guess.

        The three-way answer is the reason a vector is worth its width: a total order
        would have to say BEFORE or AFTER about two events no replica ever related.
        """
        mine_dominates = self.dominates(other)
        theirs_dominates = other.dominates(self)
        if mine_dominates and theirs_dominates:
            return Relation.EQUAL
        if mine_dominates:
            return Relation.AFTER
        if theirs_dominates:
            return Relation.BEFORE
        return Relation.CONCURRENT

    def before(self, other: VersionVector) -> bool:
        return self.compare(other) is Relation.BEFORE

    def concurrent_with(self, other: VersionVector) -> bool:
        return self.compare(other) is Relation.CONCURRENT

    def text(self) -> str:
        """The canonical form: sorted by name, so two equal vectors print the same."""
        return LIST_SEPARATOR.join(
            f"{node}{SEPARATOR}{self._counts[node]}" for node in self.nodes()
        )

    def as_dict(self) -> dict[str, object]:
        return {"counts": dict(sorted(self._counts.items())), "width": len(self._counts)}

    def __len__(self) -> int:
        return len(self._counts)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VersionVector):
            return NotImplemented
        return self._counts == other._counts

    def __hash__(self) -> int:
        return hash(tuple(sorted(self._counts.items())))

    def __repr__(self) -> str:
        return f"VersionVector({self.text() or 'empty'})"


def merge_all(vectors: list[VersionVector]) -> VersionVector:
    """Fold a list with the join. An empty list is the empty vector, not an error."""
    total = VersionVector.empty()
    for vector in vectors:
        total = total.merge(vector)
    return total


def explain(left: VersionVector, right: VersionVector) -> str:
    """The comparison as a sentence naming the counters that decided it."""
    relation = left.compare(right)
    if relation is Relation.EQUAL:
        return "equal: both vectors hold the same counters"
    if relation is Relation.CONCURRENT:
        ahead = [node for node in right.nodes() if left.get(node) < right.get(node)]
        behind = [node for node in left.nodes() if right.get(node) < left.get(node)]
        return (
            "concurrent: "
            + ", ".join(f"{node} is ahead on the right" for node in ahead)
            + "; "
            + ", ".join(f"{node} is ahead on the left" for node in behind)
        )
    smaller, larger = (left, right) if relation is Relation.BEFORE else (right, left)
    extra = [
        f"{node} {smaller.get(node)} -> {larger.get(node)}"
        for node in larger.nodes()
        if larger.get(node) > smaller.get(node)
    ]
    return f"{relation.value}: " + ", ".join(extra)
