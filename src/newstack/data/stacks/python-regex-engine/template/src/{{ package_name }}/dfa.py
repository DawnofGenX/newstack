"""One state per set of NFA states: determinisation without a backtracking engine.

The NFA carries sets of states while it runs; the DFA asks the same question up
front for every set it can reach, so at run time a single state index is enough.
The two machines are equal by construction, and the agreement check turns that
claim into an exhaustive test rather than a hope.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from . import nfa as nfa_module
from . import syntax

CAP = 200_000


@dataclass(frozen=True)
class Dfa:
    """States are sets of NFA states; `other` stands for any unmentioned char."""

    pattern: str
    subsets: tuple[frozenset[int], ...]
    start: int
    accepting: tuple[int, ...]
    transitions: tuple[tuple[int, str, int], ...]
    symbols: str
    other: str

    @property
    def states(self) -> int:
        return len(self.subsets)

    def table(self) -> dict[tuple[int, str], int]:
        return {(source, symbol): target for source, symbol, target in self.transitions}

    def symbol_for(self, char: str) -> str:
        return char if char in self.symbols else self.other

    def step(self, state: int, char: str) -> int | None:
        return self.table().get((state, self.symbol_for(char)))

    def run(self, text: str) -> list[int | None]:
        path: list[int | None] = [self.start]
        for char in text:
            last = path[-1]
            path.append(None if last is None else self.step(last, char))
        return path

    def matches(self, text: str) -> bool:
        final = self.run(text)[-1]
        return final is not None and final in self.accepting

    def accepts_prefix(self, text: str) -> int | None:
        longest = None
        for index, state in enumerate(self.run(text)):
            if state is not None and state in self.accepting:
                longest = index
        return longest

    def lines(self) -> list[str]:
        return [
            f"dfa        {self.states} state(s), {len(self.transitions)} transition(s), "
            f"{len(self.accepting)} accepting",
            f"symbols    {self.symbols!r} plus {self.other!r} for everything else",
        ]


def determinize(node: syntax.Node, text: str = "") -> Dfa:
    """Subset construction: every reachable set of NFA states becomes one state."""
    machine = nfa_module.compile_node(node, text)
    other = syntax.unmentioned_char(node)
    symbols = syntax.alphabet(node) + other
    start_set = machine.start_states()
    subsets: list[frozenset[int]] = [start_set]
    index_of: dict[frozenset[int], int] = {start_set: 0}
    transitions: list[tuple[int, str, int]] = []
    pending = 0
    while pending < len(subsets):
        current = subsets[pending]
        for symbol in symbols:
            target = machine.step(current, symbol)
            if target not in index_of:
                index_of[target] = len(subsets)
                subsets.append(target)
            transitions.append((pending, symbol, index_of[target]))
        pending += 1
    accepting = tuple(i for i, subset in enumerate(subsets) if machine.accepts(subset))
    return Dfa(
        pattern=text or node.render(),
        subsets=tuple(subsets),
        start=0,
        accepting=accepting,
        transitions=tuple(transitions),
        symbols=syntax.alphabet(node),
        other=other,
    )


@dataclass(frozen=True)
class Agreement:
    """The result of comparing both machines on every string up to a length."""

    pattern: str
    alphabet: str
    longest: int
    checked: int
    mismatches: tuple[str, ...]

    def held(self) -> bool:
        return not self.mismatches

    def lines(self) -> list[str]:
        verdict = "agree" if self.held() else "DISAGREE"
        lines = [
            f"pattern    {self.pattern}",
            f"alphabet   {self.alphabet!r} and no other character matters",
            f"checked    {self.checked} string(s) of length 0..{self.longest}",
            f"verdict    the two machines {verdict}",
        ]
        for text in self.mismatches[:5]:
            lines.append(f"           {text!r}")
        return lines


def _strings(alphabet: str, longest: int) -> list[str]:
    found: list[str] = []
    for length in range(longest + 1):
        for letters in product(alphabet, repeat=length):
            found.append("".join(letters))
            if len(found) > CAP:
                raise ValueError(
                    f"{len(found)} strings is past the {CAP} this check will enumerate; "
                    "shorten --max-len or the alphabet"
                )
    return found


def agreement(node: syntax.Node, *, alphabet: str | None = None, longest: int = 5) -> Agreement:
    """Compare the NFA and the DFA on every string over a small alphabet."""
    machine = nfa_module.compile_node(node, node.render())
    dfa = determinize(node, node.render())
    letters = alphabet if alphabet is not None else syntax.alphabet(node) + "~"
    mismatches: list[str] = []
    texts = _strings(letters, longest)
    for text in texts:
        if machine.matches(text) != dfa.matches(text):
            mismatches.append(text)
    return Agreement(
        pattern=node.render(),
        alphabet=letters,
        longest=longest,
        checked=len(texts),
        mismatches=tuple(mismatches),
    )
