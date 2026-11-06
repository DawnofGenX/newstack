"""A Merkle tree built the way RFC 6962 builds one, so its shape is not a choice.

The tree is split at the largest power of two below the leaf count. A tree that
duplicates the last node of an odd level instead (the Bitcoin shape) has a
different root for the same leaves, so a proof is only meaningful next to the
rule that produced it.
"""

from __future__ import annotations

from dataclasses import dataclass

from .hashing import HASH_BYTES, hex_of, leaf_hash, node_hash, sha256, unhex

EMPTY_ROOT = sha256(b"")


class TreeError(ValueError):
    """The tree or the proof cannot exist."""


def split_point(count: int) -> int:
    """The largest power of two strictly below count."""
    if count < 2:
        raise TreeError(f"a range of {count} leaf/leaves cannot be split")
    return 1 << ((count - 1).bit_length() - 1)


def depth(size: int) -> int:
    """The most siblings an inclusion proof for a tree of this size can carry.

    The RFC shape is not level: in a tree of five leaves, index 3 sits in the
    four-leaf left subtree and needs three siblings, while index 4 is the lone
    right leaf and needs one. `depth` is the upper bound (the bit length of
    size - 1), and `siblings_needed` is the exact count for one index.
    """
    if size < 1:
        raise TreeError("an empty tree has no leaves to prove")
    return (size - 1).bit_length()


def siblings_needed(index: int, size: int) -> int:
    """How many siblings a proof for this index of this tree actually carries."""
    if size < 1:
        raise TreeError("an empty tree has no leaves to prove")
    if not 0 <= index < size:
        raise TreeError(f"index {index} is not in a tree of {size} leaf/leaves")
    steps = 0
    low, high = 0, size
    while high - low > 1:
        point = split_point(high - low)
        if index < low + point:
            high = low + point
        else:
            low = low + point
        steps += 1
    return steps


@dataclass(frozen=True)
class Verdict:
    ok: bool
    reason: str
    recomputed: bytes = b""

    def line(self) -> str:
        return f"{'ok' if self.ok else 'refused':<8} {self.reason}"


@dataclass(frozen=True)
class Proof:
    index: int
    size: int
    leaf: str
    path: tuple[bytes, ...]
    root: bytes

    def as_dict(self) -> dict:
        return {
            "index": self.index,
            "size": self.size,
            "leaf": self.leaf,
            "path": [hex_of(item) for item in self.path],
            "root": hex_of(self.root),
        }

    @classmethod
    def from_dict(cls, payload: dict) -> Proof:
        try:
            return cls(
                index=int(payload["index"]),
                size=int(payload["size"]),
                leaf=str(payload["leaf"]),
                path=tuple(unhex(item) for item in payload["path"]),
                root=unhex(str(payload["root"])),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise TreeError(f"this is not a proof: {error}") from error

    def lines(self) -> list[str]:
        lines = [
            f"index        {self.index} of {self.size}",
            f"leaf         {self.leaf}",
            f"path         {len(self.path)} sibling(s)",
        ]
        lines.extend(f"  {position + 1}. {hex_of(item)}" for position, item in enumerate(self.path))
        lines.append(f"root         {hex_of(self.root)}")
        return lines


class Tree:
    """A tree built from leaf contents, in order."""

    __slots__ = ("_leaves",)

    def __init__(self, leaves: list[bytes]) -> None:
        self._leaves = list(leaves)

    @property
    def size(self) -> int:
        return len(self._leaves)

    @property
    def leaves(self) -> list[bytes]:
        return list(self._leaves)

    def leaf_hash(self, index: int) -> bytes:
        if not 0 <= index < self.size:
            raise TreeError(f"index {index} is not in a tree of {self.size} leaf/leaves")
        return leaf_hash(self._leaves[index])

    def root(self) -> bytes:
        if not self._leaves:
            return EMPTY_ROOT
        return self._hash_range(0, self.size)

    def _hash_range(self, low: int, high: int) -> bytes:
        count = high - low
        if count == 1:
            return leaf_hash(self._leaves[low])
        point = split_point(count)
        return node_hash(
            self._hash_range(low, low + point),
            self._hash_range(low + point, high),
        )

    def prove(self, index: int) -> Proof:
        if not 0 <= index < self.size:
            raise TreeError(f"index {index} is not in a tree of {self.size} leaf/leaves")
        path = self._path(0, self.size, index)
        return Proof(index=index, size=self.size, leaf=hex_of(leaf_hash(self._leaves[index])),
                     path=tuple(path), root=self.root())

    def _path(self, low: int, high: int, index: int) -> list[bytes]:
        count = high - low
        if count == 1:
            return []
        point = split_point(count)
        if index < low + point:
            return [*self._path(low, low + point, index),
                    self._hash_range(low + point, high)]
        return [*self._path(low + point, high, index), self._hash_range(low, low + point)]

    def verify(self, index: int, leaf: bytes, path: tuple[bytes, ...] | list[bytes]) -> Verdict:
        """Check one proof against this tree's own root and size."""
        return verify(index, leaf, path, root=self.root(), size=self.size)


def verify(
    index: int,
    leaf: bytes,
    path: tuple[bytes, ...] | list[bytes],
    *,
    root: bytes,
    size: int,
) -> Verdict:
    """Recompute the root from one leaf and the siblings, and compare."""
    if size < 1:
        return Verdict(False, "an empty tree has no leaf to prove")
    if not 0 <= index < size:
        return Verdict(False, f"index {index} is not in a tree of {size} leaf/leaves")
    # The path is stored nearest-sibling-first, and the walk starts at the root,
    # so the last element is the first one consumed.
    siblings = list(path)
    for sibling in siblings:
        if len(sibling) != HASH_BYTES:
            return Verdict(False, f"a sibling is {len(sibling)} byte(s), not {HASH_BYTES}")
    needed = siblings_needed(index, size)
    if len(siblings) != needed:
        return Verdict(
            False,
            f"the proof carries {len(siblings)} sibling(s) but index {index} of a tree of "
            f"{size} needs {needed}",
        )
    # Folding is bottom-up, so first walk down from the root recording which
    # side the leaf took at each level, then apply those decisions in reverse
    # against the path, which is stored nearest-sibling-first.  Consuming the
    # path from the top of the tree (or walking up without reversing the
    # decisions) combines a half-folded hash with a sibling from the wrong
    # level, and every honest proof is refused.
    sides: list[bool] = []
    low, high = 0, size
    while high - low > 1:
        point = split_point(high - low)
        if index < low + point:
            sides.append(True)
            high = low + point
        else:
            sides.append(False)
            low = low + point
    current = leaf_hash(leaf)
    for is_left, sibling in zip(reversed(sides), siblings, strict=True):
        current = node_hash(current, sibling) if is_left else node_hash(sibling, current)
    steps = len(sides)
    if current == root:
        return Verdict(True, f"the proof recomputes the root in {steps} step(s)", current)
    return Verdict(
        False,
        f"the proof recomputes {hex_of(current)[:16]}… but the root is {hex_of(root)[:16]}…",
        current,
    )
