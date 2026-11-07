"""The merge ladder: lightest two first, ties falling alphabetically.

build_tree(frequencies) answers with a Node tree, and the ladder
is deterministic by rule: every step takes the two cheapest
entries left on the ladder — never the third-cheapest — weights
first, leaves ahead of branches, letters in alphabetical order,
and every freshly forged branch waiting behind every branch
forged before it. So the same weights always build the same tree,
letter for letter, and the walk and the table never disagree.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .freq import Frequency, ensure_frequencies
from .text import LETTERS

if TYPE_CHECKING:
    from .table import CodeTable


class TreeError(ValueError):
    """A tree was asked for where no tree answers."""

    __slots__ = ()


@dataclass(frozen=True)
class Leaf:
    """A letter and the weight it carries."""

    letter: str
    weight: int

    def __post_init__(self) -> None:
        if self.letter not in LETTERS:
            raise TreeError(f"{self.letter!r} is not a lowercase letter")
        if self.weight <= 0:
            raise TreeError(f"a leaf weighs positive, not {self.weight}")


@dataclass(frozen=True)
class Branch:
    """Two subtrees; the branch weighs what they weigh together."""

    left: Node
    right: Node

    @property
    def weight(self) -> int:
        return _weight(self.left) + _weight(self.right)


Node = Leaf | Branch


def _weight(node: Node) -> int:
    return node.weight


def build_tree(frequencies: Frequency) -> Node:
    """The deterministic ladder: the two cheapest left, ties alphabetical."""
    clean = ensure_frequencies(frequencies)
    if not clean:
        raise TreeError("no tree from no letters")
    ladder: list[tuple[int, int, int, Node]] = [
        (weight, 0, ord(letter), Leaf(letter, weight))
        for letter, weight in clean.items()
    ]
    forged = 0
    while len(ladder) > 1:
        ladder.sort()
        left = ladder.pop(0)[3]
        right = ladder.pop(0)[3]
        forged += 1
        ladder.append((left.weight + right.weight, 1, forged, Branch(left, right)))
    return ladder[0][3]


def walk(node: Node, bits: str) -> str:
    """Walk the tree by bits: '0' left, '1' right, a word ends on a letter."""
    if not bits:
        raise TreeError("an empty bit string names no word")
    current: Node = node
    for bit in bits:
        if isinstance(current, Leaf):
            raise TreeError(f"{bits!r} runs past the letter it reached")
        if bit == "0":
            current = current.left
        elif bit == "1":
            current = current.right
        else:
            raise TreeError(f"{bit!r} is no bit")
    if not isinstance(current, Leaf):
        raise TreeError(f"{bits!r} stops inside the tree, not on a letter")
    return current.letter


def depths(node: Node, at: int = 0) -> dict[str, int]:
    """Harvest every letter with the length of its road home."""
    if isinstance(node, Leaf):
        return {node.letter: at}
    harvest = depths(node.left, at + 1)
    harvest.update(depths(node.right, at + 1))
    return harvest


def height(node: Node) -> int:
    """The longest root-to-leaf road: the priciest word the tree pays."""
    if isinstance(node, Leaf):
        return 0
    return 1 + max(height(node.left), height(node.right))


def walk_table_agreement(tree: Node, table: CodeTable) -> bool:
    """The ladder and the table agree: same letters, roads of the right
    length, and a wordlist that answers nowhere twice.

    Three checks, one claim: the harvest and the wordlist name the
    same letters; every shipped word is exactly as long as its
    letter's road through the ladder; and the wordlist is prefix-free
    — no shipped code opens where another one closes. A canonical
    table answers through its own wordlist, never by replaying the
    ladder's turns, so the ladder is asked for lengths, not roads.
    """
    harvest = depths(tree)
    if sorted(harvest) != sorted(table.codes):
        return False
    roads = sorted(max(depth, 1) for depth in harvest.values())
    if sorted(len(word) for word in table.codes.values()) != roads:
        return False
    words = list(table.codes.values())
    if len(set(words)) != len(words):
        return False
    return not any(
        other != word and other.startswith(word) for word in words for other in words
    )
