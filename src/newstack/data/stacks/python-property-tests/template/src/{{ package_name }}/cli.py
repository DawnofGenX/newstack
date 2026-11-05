"""Command line entry point: a coverage calculator plus a shrinking demonstration."""

from __future__ import annotations

import itertools
import sys
from collections.abc import Sequence

from . import __version__
from .intervals import Interval, coverage, normalize

# The rendered project name, kept in one place so a long one does not stretch every
# error message past the 100-column lint budget.
PROGRAM = "{{ npm_name }}"

USAGE = """usage: {{ npm_name }} <command> [options]

commands
  cover START END [START END ...]   print how many points the intervals cover
  demo                              show the smallest input that fools a naive sum
  --selftest                        run the offline checks
  --version                         print the version
"""


def naive_coverage(items: Sequence[Interval]) -> int:
    """The bug this stack exists to catch: sum the lengths and forget the overlaps.

    It is right whenever the input is already normalised, which is exactly why
    example-based tests miss it - the failure needs two overlapping intervals, and
    the smallest such input is not the kind of thing a person types by hand.
    """
    return sum(item.length for item in items if not item.empty)


def minimal_counterexample(universe: int = 2) -> tuple[list[Interval], int, int]:
    """Search the smallest inputs for one where ``naive_coverage`` disagrees.

    The search is exhaustive over lists of at most two intervals inside a tiny
    universe, so the answer is the true minimum rather than the first thing a
    random draw happened to find. Hypothesis does the same job at scale by
    shrinking a random failure; this keeps the demo deterministic and fast.
    """
    candidates = [
        Interval(start, end) for start in range(universe) for end in range(start + 1, universe + 1)
    ]
    for size in (1, 2, 3):
        for combination in itertools.combinations_with_replacement(candidates, size):
            naive = naive_coverage(combination)
            real = coverage(combination)
            if naive != real:
                return list(combination), naive, real
    raise RuntimeError(f"no counterexample inside a universe of {universe}")


def _parse_pairs(values: Sequence[str]) -> list[Interval]:
    if len(values) % 2:
        raise ValueError("start and end arrive in pairs: cover 0 10 20 30")
    pairs = []
    for index in range(0, len(values), 2):
        start, end = int(values[index]), int(values[index + 1])
        pairs.append(Interval(start, end))
    return pairs


def _demo() -> int:
    items, naive, real = minimal_counterexample()
    shown = ", ".join(f"[{item.start}, {item.end})" for item in items)
    print(f"smallest input that fools a naive sum: {shown}")
    print(f"naive sum {naive}   real coverage {real}")
    print(f"normalized: {', '.join(f'[{i.start}, {i.end})' for i in normalize(items))}")
    print("hypothesis finds this shape by shrinking a random failure; the demo searches for it")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in {"-h", "--help", "help"}:
        print(USAGE, end="")
        return 0
    if argv and argv[0] in {"-V", "--version"}:
        print(f"{PROGRAM} {__version__}")
        return 0
    if argv and argv[0] == "--selftest":
        from .selftest import run

        return run()
    if not argv:
        print(USAGE, end="", file=sys.stderr)
        return 2
    command, rest = argv[0], argv[1:]
    if command == "demo":
        return _demo()
    if command == "cover":
        try:
            pairs = _parse_pairs(rest)
        except ValueError as exc:
            print(f"{PROGRAM}: {exc}", file=sys.stderr)
            return 2
        if not pairs:
            print(f"{PROGRAM}: cover needs at least one START END pair", file=sys.stderr)
            return 2
        print(coverage(pairs))
        return 0
    print(f"{PROGRAM}: unknown command {command!r}\n", file=sys.stderr)
    print(USAGE, end="", file=sys.stderr)
    return 2
