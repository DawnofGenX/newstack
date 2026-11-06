"""Aho-Corasick: every pattern at once, one sweep, no backtracking.

The trie holds the patterns; the failure links are built breadth-first and
each one fails forward to a shorter suffix, so a state that stops matching mid-pattern
lands on the longest proper suffix that is still a prefix of something. A
state reports not only the patterns ending on it but every pattern ending on
its failure chain, which is how 'he' is still reported inside 'she'. One
pass over the text reports every (pattern, end-position) pair.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from .corpus import as_patterns

__all__ = ["AhoCorasick", "AhoCorasickError", "Hit", "Sweep"]


class AhoCorasickError(ValueError):
    """The pattern set does not describe an automaton that can be built."""


@dataclass(frozen=True, order=True)
class Hit:
    """One reported match: this pattern ended here, starting there."""

    end: int
    start: int
    pattern: str

    def describe(self) -> str:
        return f"{self.pattern!r} ends at {self.end} (spans {self.start}..{self.end})"


@dataclass(frozen=True)
class Sweep:
    """One pass over a text: the hits it reported and the states it crossed."""

    hits: tuple[Hit, ...]
    states: int
    text_length: int

    def __len__(self) -> int:
        return len(self.hits)


class _Node:
    """One state of the trie: a prefix, its children, its failure, its outputs."""

    __slots__ = ("children", "depth", "fail", "outputs", "terms")

    def __init__(self, depth: int = 0) -> None:
        self.children: dict[str, _Node] = {}
        self.depth = depth
        self.fail: _Node = self
        self.terms: tuple[str, ...] = ()
        self.outputs: tuple[str, ...] = ()


class AhoCorasick:
    """A trie plus BFS failure links: build once, sweep any number of texts.

    Duplicate patterns are deduped at build time (documented, not an error).
    An empty pattern set is legal: its sweep reports nothing, forever.
    A blank pattern is refused because it would match at every boundary.
    """

    def __init__(self, patterns: object = ()) -> None:
        self._root = _Node()
        self._patterns: list[str] = []
        for raw in as_patterns(patterns):
            if not isinstance(raw, str):
                raise AhoCorasickError(f"pattern {raw!r} is not a string")
            if not raw:
                raise AhoCorasickError("a blank pattern would match everywhere")
            if raw in self._patterns:
                continue
            self._patterns.append(raw)
            self._absorb(raw)
        self._link()

    @property
    def root(self) -> _Node:
        return self._root

    @property
    def patterns(self) -> tuple[str, ...]:
        return tuple(self._patterns)

    @property
    def states(self) -> int:
        """Every state of the trie, the root included."""
        return 1 + sum(1 for _ in self._walk())

    @property
    def depth(self) -> int:
        """The longest root-to-state walk, so the longest pattern prefix."""
        return max((node.depth for node in self._walk()), default=0)

    def _absorb(self, pattern: str) -> None:
        node = self._root
        for char in pattern:
            node = node.children.setdefault(char, _Node(node.depth + 1))
        node.terms = (*node.terms, pattern)

    def _link(self) -> None:
        """Failure links and output chains, breadth-first, shortest first."""
        self._root.fail = self._root
        self._root.outputs = self._root.terms
        queue = deque()
        for child in self._root.children.values():
            child.fail = self._root
            child.outputs = child.terms + self._root.outputs
            queue.append(child)
        while queue:
            parent = queue.popleft()
            for char, child in parent.children.items():
                queue.append(child)
                step = parent.fail
                while step is not self._root and char not in step.children:
                    step = step.fail
                target = step.children.get(char, self._root)
                child.fail = self._root if target is child else target
                child.outputs = child.terms + child.fail.outputs

    def _walk(self):
        """Every state below the root, in no particular promised order."""
        stack = list(self._root.children.values())
        while stack:
            node = stack.pop()
            yield node
            stack.extend(node.children.values())

    def sweep(self, text: str) -> Sweep:
        """One pass over the text; never rewinds, never re-reads a character."""
        if not isinstance(text, str):
            raise AhoCorasickError(f"text {text!r} is not a string")
        found: list[Hit] = []
        state = self._root
        crossings = 0
        for index, char in enumerate(text):
            while state is not self._root and char not in state.children:
                state = state.fail
                crossings += 1
            state = state.children.get(char, self._root)
            crossings += 1
            for pattern in state.outputs:
                found.append(Hit(index, index - len(pattern) + 1, pattern))
        found.sort(key=lambda hit: (hit.end, hit.start, hit.pattern))
        return Sweep(tuple(found), crossings, len(text))

    def scan(self, text: str) -> tuple[Hit, ...]:
        """The hits only: the sweep's ledger lives in sweep()."""
        return self.sweep(text).hits

    def count(self, text: str) -> int:
        """How many hits one sweep reports; a counter's whole question."""
        return len(self.sweep(text))
