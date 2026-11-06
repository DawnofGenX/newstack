"""Deciding whether a history has a linearization.

The search walks the operations in every order that respects two things: each
client's programme order, and real time (an operation that responded before
another invoked must be linearized first). A read is only allowed where the
register already holds the value it returned. The search is exhaustive, so a
"no" is a proof by elimination, not a timeout -- and where a "no" is found, the
history is shrunk until removing any single operation makes it linearizable.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

from .history import READ, History, Operation


@dataclass(frozen=True)
class Outcome:
    linearizable: bool
    order: tuple[int, ...] = ()
    nodes: int = 0
    memo_hits: int = 0
    reason: str = ""

    @property
    def verdict(self) -> str:
        return "linearizable" if self.linearizable else "not linearizable"

    def as_dict(self) -> dict[str, object]:
        return {
            "linearizable": self.linearizable,
            "order": list(self.order),
            "nodes": self.nodes,
            "memo_hits": self.memo_hits,
            "reason": self.reason,
        }


def _programme_heads(history: History) -> dict[int, list[int]]:
    heads: dict[int, list[int]] = {}
    for index, op in enumerate(history.operations):
        heads.setdefault(op.client, []).append(index)
    return heads


def _may_be_next(ops: tuple[Operation, ...], index: int, remaining: frozenset[int]) -> bool:
    """False when some unlinearized operation responded before this one invoked."""
    starts = ops[index].start
    return all(ops[other].end >= starts for other in remaining)


def check(history: History, *, initial: int | None = None) -> Outcome:
    ops = history.operations
    count = len(ops)
    if count == 0:
        return Outcome(True, (), 0, 0, "the empty history is linearizable")
    start_value = history.initial if initial is None else initial
    heads = _programme_heads(history)
    pointers = {client: 0 for client in heads}
    remaining = frozenset(range(count))
    failed: set[tuple[frozenset[int], int]] = set()
    order: list[int] = []
    nodes = 0
    hits = 0

    def search(rest: frozenset[int], value: int) -> bool:
        nonlocal nodes, hits
        if not rest:
            return True
        key = (rest, value)
        if key in failed:
            hits += 1
            return False
        nodes += 1
        candidates: list[int] = []
        for client, indexes in heads.items():
            pointer = pointers[client]
            if pointer >= len(indexes):
                continue
            index = indexes[pointer]
            if index in rest and _may_be_next(ops, index, rest):
                candidates.append(index)
        candidates.sort()
        for index in candidates:
            op = ops[index]
            if op.kind == READ and op.value != value:
                continue
            pointers[op.client] += 1
            order.append(index)
            wrote = value if op.kind == READ else op.value
            if search(rest - {index}, wrote):
                return True
            order.pop()
            pointers[op.client] -= 1
        failed.add(key)
        return False

    if search(remaining, start_value):
        return Outcome(
            True,
            tuple(order),
            nodes,
            hits,
            f"a witness order of {count} operation(s) exists",
        )
    reason = (
        f"no order of the {count} operation(s) agrees with the per-client order, "
        "the real-time order and the values the reads returned"
    )
    return Outcome(False, (), nodes, hits, reason)


def brute_force(history: History, *, initial: int | None = None) -> Outcome:
    """Every permutation, for tiny histories only: the yardstick for the search's pruning."""
    ops = history.operations
    count = len(ops)
    start_value = history.initial if initial is None else initial
    if count == 0:
        return Outcome(True, (), 0, 0, "the empty history is linearizable")
    if count > 8:
        raise ValueError(
            f"{count} operations is {_factorial(count)} permutations; brute force stops at 8"
        )
    headings = _programme_heads(history)
    position = {
        index: (client, place)
        for client, indexes in headings.items()
        for place, index in enumerate(indexes)
    }
    tried = 0
    for candidate in itertools.permutations(range(count)):
        tried += 1
        seen: dict[int, int] = {client: -1 for client in headings}
        value = start_value
        ok = True
        for index in candidate:
            client, place = position[index]
            if place != seen[client] + 1:
                ok = False
                break
            seen[client] = place
            op = ops[index]
            if op.kind == READ:
                if op.value != value:
                    ok = False
                    break
            else:
                value = op.value
        if not ok:
            continue
        if _real_time_holds(ops, candidate):
            return Outcome(
                True, candidate, tried, 0, f"the first order that holds took {tried} tries"
            )
    return Outcome(False, (), tried, 0, f"none of the {tried} permutations holds")


def _real_time_holds(ops: tuple[Operation, ...], order: tuple[int, ...]) -> bool:
    place = {index: spot for spot, index in enumerate(order)}
    for first, second in itertools.combinations(order, 2):
        if ops[first].end < ops[second].start and place[second] < place[first]:
            return False
        if ops[second].end < ops[first].start and place[first] < place[second]:
            return False
    return True


def _factorial(number: int) -> int:
    total = 1
    for step in range(2, number + 1):
        total *= step
    return total


def shrink(history: History) -> tuple[History, Outcome]:
    """Drop operations while the history stays unlinearizable, one at a time."""
    verdict = check(history)
    if verdict.linearizable:
        return history, verdict
    keep = list(range(len(history.operations)))
    changed = True
    while changed:
        changed = False
        for index in list(keep):
            trial = [spot for spot in keep if spot != index]
            if not check(history.restricted(trial)).linearizable:
                keep = trial
                changed = True
                break
    core = history.restricted(keep)
    return core, check(core)


def is_minimal(core: History) -> bool:
    """True when dropping any single operation from the core makes it linearizable."""
    if check(core).linearizable:
        return False
    if len(core) <= 1:
        return True
    for index in range(len(core)):
        trial = [spot for spot in range(len(core)) if spot != index]
        if not check(core.restricted(trial)).linearizable:
            return False
    return True
