"""The sorted map itself: towers of nodes, walked one coin flip at a time.

A node stores a key, a value, and one forward link per story it stands
on. Every link carries its width: how many slots at the bottom lane it
spans, counted as destination-index minus source-index. Widths are what
make `rank` and `select` cost one walk instead of one scan — rank sums
the widths it skips over, select walks widths down to a position, and
because every insert and delete repairs every affected width, the two
are exact inverses without ever sorting.

Same seed, same insertion order, byte-identical shape.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from .coins import DEFAULT_SEED, CoinToss, expected_level
from .keys import SkipKeyValueError, describe, ensure_key

__all__ = ["Edit", "SkipList", "SkipListError", "Walk"]

MAX_LEVEL = 16


class SkipListError(SkipKeyValueError):
    """The map was asked something no ordered map can answer."""


class _Node:
    __slots__ = ("forward", "key", "value", "width")

    def __init__(self, key: object, value: object, height: int) -> None:
        self.key = key
        self.value = value
        self.forward: list[_Node | None] = [None] * height
        self.width: list[int] = [0] * height

    @property
    def height(self) -> int:
        return len(self.forward)


@dataclass(frozen=True)
class Edit:
    """What one insert or delete cost: probes, relinks, and the height."""

    key: object
    changed: bool
    probes: int
    relinks: int
    level: int

    def line(self) -> str:
        verb = "insert" if self.changed else "repeat"
        return (
            f"{verb:8} {describe(self.key)!r:>12} level {self.level} "
            f"probes {self.probes} relinks {self.relinks}"
        )


@dataclass(frozen=True)
class Walk:
    """One read: the answer, and how far the walk travelled to get it."""

    answer: object
    probes: int
    hops: int
    deepest: int

    def line(self) -> str:
        return f"{describe(self.answer)!r:>12} probes {self.probes} hops {self.hops}"


def _before(left: object, right: object) -> bool:
    return left < right  # type: ignore[operator]


class SkipList:
    """A map that stays sorted because towers, not rotations, balance it.

    Heights come from one seeded toss, so two maps fed the same pairs in
    the same order end up identical in shape. Link widths turn order
    into arithmetic: `rank` asks how many keys sit strictly below,
    `select` asks who sits at a position, and the selftest checks both
    against `bisect` on a plain sorted list.
    """

    def __init__(self, seed: int = DEFAULT_SEED, max_level: int = MAX_LEVEL) -> None:
        if max_level < 2:
            raise SkipListError(f"a tower cap of {max_level} holds nothing")
        self.max_level = max_level
        self._toss = CoinToss(seed)
        self._head = _Node(None, None, max_level)
        self._size = 0

    def __len__(self) -> int:
        return self._size

    @property
    def seed(self) -> int:
        return self._toss.seed

    @property
    def height(self) -> int:
        for level in range(self.max_level - 1, -1, -1):
            if self._head.forward[level] is not None:
                return level + 1
        return 1

    def _cap(self) -> int:
        limit = expected_level(max(self._size, 2)) + 2
        return min(self.max_level, max(2, limit))

    def _search(
        self, tagged: object
    ) -> tuple[list[_Node | None], list[int], int, _Node | None]:
        """High to low: predecessors, their slots, probes, and the exact hit."""
        probes = 0
        slot = 0
        node = self._head
        stack: list[_Node | None] = [self._head] * self.max_level
        slots: list[int] = [0] * self.max_level
        for level in range(self.max_level - 1, -1, -1):
            nxt = node.forward[level]
            while nxt is not None and _before(nxt.key, tagged):
                slot += node.width[level]
                node = nxt
                probes += 1
                nxt = node.forward[level]
            stack[level] = node
            slots[level] = slot
        hit = node.forward[0]
        if hit is None or hit.key != tagged:
            hit = None
        return stack, slots, probes, hit

    def insert(self, key: Any, value: Any = None) -> Edit:
        """Put the pair in place; a repeat replaces the value, not the slot."""
        tagged = ensure_key(key)
        stack, slots, probes, found = self._search(tagged)
        if found is not None:
            found.value = value
            return Edit(key, False, probes, 0, 0)
        floor = slots[0] + 1
        level = self._toss.level(self._cap())
        node = _Node(tagged, value, level + 1)
        for story in range(level + 1):
            back = stack[story]
            ahead = back.forward[story]
            reach = slots[story] + back.width[story] if ahead is not None else self._size
            node.forward[story] = ahead
            node.width[story] = reach - floor + 1 if ahead is not None else 1
            back.forward[story] = node
            back.width[story] = floor - slots[story]
        for story in range(level + 1, self.max_level):
            back = stack[story]
            if back.forward[story] is not None:
                back.width[story] += 1
        self._size += 1
        return Edit(key, True, probes, level + 1, level)

    def delete(self, key: Any) -> Edit:
        """Take the pair out; every story it stood on is unlinked."""
        tagged = ensure_key(key)
        stack, _, probes, node = self._search(tagged)
        if node is None:
            return Edit(key, False, probes, 0, 0)
        stories = node.height
        for story in range(stories):
            back = stack[story]
            if back.forward[story] is not node:
                raise SkipListError(f"{describe(key)!r} lost its link at level {story}")
            back.forward[story] = node.forward[story]
            back.width[story] = back.width[story] + node.width[story] - 1
        for story in range(stories, self.max_level):
            back = stack[story]
            if back.forward[story] is not None:
                back.width[story] -= 1
        self._size -= 1
        return Edit(key, True, probes, stories, stories)

    def contains(self, key: Any) -> bool:
        return self._locate(key) is not None

    def get(self, key: Any, default: Any = None) -> Any:
        """The stored value, or default when the key is not in the map."""
        node = self._locate(key)
        return default if node is None else node.value

    def _locate(self, key: Any) -> _Node | None:
        _, _, _, hit = self._search(ensure_key(key))
        return hit

    def rank(self, key: Any) -> int:
        """How many stored keys sit strictly below this one."""
        tagged = ensure_key(key)
        slot = 0
        node = self._head
        for level in range(self.height - 1, -1, -1):
            nxt = node.forward[level]
            while nxt is not None and _before(nxt.key, tagged):
                slot += node.width[level]
                node = nxt
                nxt = node.forward[level]
        return slot

    def select(self, position: int) -> tuple[object, object]:
        """The (key, value) pair sitting at `position` in sorted order."""
        if not isinstance(position, int) or isinstance(position, bool):
            raise SkipListError(f"{position!r} is not a position")
        if not 0 <= position < self._size:
            raise SkipListError(f"position {position} of {self._size} is out of range")
        target = position + 1
        node = self._head
        slot = 0
        for level in range(self.height - 1, -1, -1):
            nxt = node.forward[level]
            while nxt is not None and slot + node.width[level] < target:
                slot += node.width[level]
                node = nxt
                nxt = node.forward[level]
        hit = node.forward[0]
        if hit is None:
            raise SkipListError(f"position {position} ran off the map")
        return hit.key, hit.value

    def predecessor(self, key: Any) -> object | None:
        """The largest stored key strictly below this one, or None."""
        below = self.rank(key)
        return None if below == 0 else self.select(below - 1)[0]

    def successor(self, key: Any) -> object | None:
        """The smallest stored key strictly above this one, or None."""
        above = self.rank(key) + (1 if self._locate(key) is not None else 0)
        return None if above >= self._size else self.select(above)[0]

    def items(self) -> Iterator[tuple[object, object]]:
        node = self._head.forward[0]
        while node is not None:
            yield node.key, node.value
            node = node.forward[0]

    def keys(self) -> Iterator[object]:
        for key, _ in self.items():
            yield key

    def values(self) -> Iterator[object]:
        for _, value in self.items():
            yield value

    def __iter__(self) -> Iterator[object]:
        return self.keys()

    def pairs(self) -> list[tuple[object, object]]:
        return list(self.items())

    def window(self, low: Any, high: Any) -> list[tuple[object, object]]:
        """Every pair with low <= key <= high, in order, without sorting."""
        start = ensure_key(low)
        stop = ensure_key(high)
        if _before(stop, start):
            raise SkipListError(f"{describe(high)!r} sorts before {describe(low)!r}")
        node = self._head
        for level in range(self.height - 1, -1, -1):
            while node.forward[level] is not None and _before(
                node.forward[level].key, start
            ):
                node = node.forward[level]
        out: list[tuple[object, object]] = []
        node = node.forward[0]
        while node is not None and not _before(stop, node.key):
            out.append((node.key, node.value))
            node = node.forward[0]
        return out

    def stats(self) -> dict[str, object]:
        """Shape facts the selftest compares against log2(size)."""
        levels = [0] * self.max_level
        tallest = 0
        node = self._head.forward[0]
        while node is not None:
            levels[node.height - 1] += 1
            tallest = max(tallest, node.height)
            node = node.forward[0]
        return {
            "size": self._size,
            "height": self.height,
            "levels": tuple(levels),
            "tallest": tallest,
            "expected_height": expected_level(self._size) if self._size else 0,
            "flips": self._toss.flips,
            "seed": self._toss.seed,
        }

    def rebuild(self) -> SkipList:
        """Same seed, same pairs, inserted in order: an identical twin."""
        twin = SkipList(self._toss.seed, self.max_level)
        for key, value in self.pairs():
            twin.insert(key, value)
        return twin

    def lines(self) -> list[str]:
        out = [f"size {self._size} height {self.height} seed {self._toss.seed}"]
        for level in range(min(self.height, 8)):
            row: list[str] = []
            node = self._head.forward[level]
            while node is not None:
                row.append(describe(node.key))
                node = node.forward[level]
            out.append(f"  L{level}  " + " ".join(row))
        return out
