"""Splitting an amount so the parts add up to it — the largest-remainder method.

`100.00 / 3` is `33.33` three times, and 99.99 is not 100.00. Every splitter that multiplies a
float by a ratio and rounds each share loses a cent per call; at scale that is a reconciliation
ticket. The method here is integer-only and exact:

1. give every share `total * ratio // weight_sum` (floor),
2. hand the leftover units out one at a time, to the shares with the largest fractional
   remainder, ties broken by position,
3. assert the result sums back to the total, because an allocator that cannot balance is worse
   than one that refuses.
"""

from __future__ import annotations

from collections.abc import Sequence

from .errors import AllocationError
from .model import Money


def allocate(money: Money, ratios: Sequence[int]) -> list[Money]:
    """Split `money` in proportion to `ratios`, with every part an exact minor-unit count."""
    if not ratios:
        raise AllocationError("allocate() needs at least one ratio")
    for ratio in ratios:
        if isinstance(ratio, bool) or not isinstance(ratio, int):
            raise AllocationError(f"ratios must be integers, got {ratio!r}")
        if ratio < 0:
            raise AllocationError(f"ratios cannot be negative, got {ratio}")
    weight = sum(ratios)
    if weight == 0:
        raise AllocationError("ratios sum to zero, so there is no proportion to apply")

    units = abs(money.amount)
    sign = -1 if money.amount < 0 else 1
    # The remainder is computed with integers on purpose: `(units * ratio) % weight` is exact,
    # while the float version of the same expression misranks fractions above 2**53.
    remainders = [(units * ratio) % weight for ratio in ratios]
    shares = [(units * ratio) // weight for ratio in ratios]
    leftover = units - sum(shares)
    order = sorted(range(len(ratios)), key=lambda index: (-remainders[index], index))
    for index in order[:leftover]:
        shares[index] += 1

    parts = [Money(sign * share, money.currency) for share in shares]
    if sum(part.amount for part in parts) != money.amount:
        raise AllocationError("allocation did not balance; this is a bug, not a rounding error")
    return parts


def split(money: Money, parts: int) -> list[Money]:
    """Split into `parts` equal shares, the remainder going to the earliest shares."""
    if parts < 1:
        raise AllocationError("split() needs at least one part")
    return allocate(money, [1] * parts)
