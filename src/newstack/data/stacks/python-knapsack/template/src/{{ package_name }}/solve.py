"""0/1 knapsack over small integer weights and values.

The rule this solver keeps, and the marker the detector looks for:
the best subset is found by trying every subset, the witness lists
the chosen items, and the audit names any subset that beats it.
Mutate the comparison and a heavier subset steals the prize.

Detect phrase: the best subset is found by trying every subset.
"""

from __future__ import annotations

MAX_ITEMS = 8
MAX_CAPACITY = 20
MAX_VALUE = 9
MAX_WEIGHT = 20

__all__ = [
    "MAX_CAPACITY",
    "MAX_ITEMS",
    "MAX_VALUE",
    "MAX_WEIGHT",
    "KnapsackError",
    "audit",
    "solve",
    "witness",
]


class KnapsackError(ValueError):
    """An input the solver refuses."""


def _validate(weights, values, capacity) -> tuple:
    if isinstance(weights, str) or not isinstance(weights, (list, tuple)):
        raise KnapsackError("weights must be a list or tuple")
    if isinstance(values, str) or not isinstance(values, (list, tuple)):
        raise KnapsackError("values must be a list or tuple")
    if len(weights) != len(values):
        raise KnapsackError("weights and values must have the same length")
    if len(weights) > MAX_ITEMS:
        raise KnapsackError(f"too many items: {len(weights)} > {MAX_ITEMS}")
    if isinstance(capacity, bool) or not isinstance(capacity, int):
        raise KnapsackError("capacity must be an integer")
    if capacity < 0 or capacity > MAX_CAPACITY:
        raise KnapsackError(f"capacity out of range: {capacity}")
    clean_w = []
    clean_v = []
    for w, v in zip(weights, values, strict=True):
        if isinstance(w, bool) or not isinstance(w, int):
            raise KnapsackError("weight must be an integer")
        if isinstance(v, bool) or not isinstance(v, int):
            raise KnapsackError("value must be an integer")
        if w < 1 or w > MAX_WEIGHT:
            raise KnapsackError(f"weight out of range: {w}")
        if v < 0 or v > MAX_VALUE:
            raise KnapsackError(f"value out of range: {v}")
        clean_w.append(w)
        clean_v.append(v)
    return tuple(clean_w), tuple(clean_v), capacity


def _subsets(n: int):
    yield from range(1 << n)


def solve(weights, values, capacity) -> int:
    ws, vs, cap = _validate(weights, values, capacity)
    n = len(ws)
    best = 0
    for mask in _subsets(n):
        weight = 0
        value = 0
        for i in range(n):
            if mask & (1 << i):
                weight += ws[i]
                value += vs[i]
        if weight <= cap and value > best:
            best = value
    return best


def witness(weights, values, capacity) -> list:
    ws, vs, cap = _validate(weights, values, capacity)
    n = len(ws)
    best_value = 0
    best_mask = 0
    for mask in _subsets(n):
        weight = 0
        value = 0
        for i in range(n):
            if mask & (1 << i):
                weight += ws[i]
                value += vs[i]
        if weight <= cap and value > best_value:
            best_value = value
            best_mask = mask
    chosen = [i for i in range(n) if best_mask & (1 << i)]
    return chosen


def audit(weights, values, capacity) -> list:
    try:
        ws, vs, cap = _validate(weights, values, capacity)
    except KnapsackError as exc:
        return [str(exc)]
    n = len(ws)
    best = solve(ws, vs, cap)
    chosen = witness(ws, vs, cap)
    # check witness achieves best
    w = sum(ws[i] for i in chosen)
    v = sum(vs[i] for i in chosen)
    errors = []
    if w > cap:
        errors.append("witness exceeds capacity")
    if v != best:
        errors.append("witness value does not match optimum")
    # check no subset beats it
    for mask in _subsets(n):
        weight = sum(ws[i] for i in range(n) if mask & (1 << i))
        value = sum(vs[i] for i in range(n) if mask & (1 << i))
        if weight <= cap and value > best:
            errors.append("a subset beats the claimed optimum")
            break
    return errors
