"""Minimum coins to make an amount from unlimited denominations.

The rule this solver keeps, and the marker the detector looks for:
the fewest coins come from trying every remainder, the witness
lists the coins used, and the audit names any cheaper way.
Mutate the relaxation and a heavier way steals the answer.

Detect phrase: the fewest coins come from trying every remainder.
"""

from __future__ import annotations

MAX_COINS = 6
MAX_AMOUNT = 30
MAX_DENOM = 20

__all__ = [
    "MAX_AMOUNT",
    "MAX_COINS",
    "MAX_DENOM",
    "CoinChangeError",
    "audit",
    "solve",
    "witness",
]


class CoinChangeError(ValueError):
    """An input the solver refuses."""


def _validate(coins, amount) -> tuple:
    if isinstance(coins, str) or not isinstance(coins, (list, tuple)):
        raise CoinChangeError("coins must be a list or tuple")
    if isinstance(amount, bool) or not isinstance(amount, int):
        raise CoinChangeError("amount must be an integer")
    if len(coins) == 0 or len(coins) > MAX_COINS:
        raise CoinChangeError(f"coin count out of range: {len(coins)}")
    if amount < 0 or amount > MAX_AMOUNT:
        raise CoinChangeError(f"amount out of range: {amount}")
    clean = []
    for c in coins:
        if isinstance(c, bool) or not isinstance(c, int):
            raise CoinChangeError("coin must be an integer")
        if c < 1 or c > MAX_DENOM:
            raise CoinChangeError(f"coin out of range: {c}")
        clean.append(c)
    return tuple(clean), amount


def solve(coins, amount) -> int:
    cs, amt = _validate(coins, amount)
    if amt == 0:
        return 0
    INF = amt + 1
    dist = [INF] * (amt + 1)
    dist[0] = 0
    for a in range(1, amt + 1):
        for c in cs:
            if a - c >= 0 and dist[a - c] + 1 < dist[a]:
                dist[a] = dist[a - c] + 1
    return dist[amt] if dist[amt] != INF else -1


def witness(coins, amount) -> list:
    cs, amt = _validate(coins, amount)
    if amt == 0:
        return []
    INF = amt + 1
    dist = [INF] * (amt + 1)
    parent = [-1] * (amt + 1)
    dist[0] = 0
    for a in range(1, amt + 1):
        for c in cs:
            if a - c >= 0 and dist[a - c] + 1 < dist[a]:
                dist[a] = dist[a - c] + 1
                parent[a] = c
    if dist[amt] == INF:
        return []
    out = []
    a = amt
    while a > 0:
        c = parent[a]
        out.append(c)
        a -= c
    return out


def audit(coins, amount) -> list:
    try:
        cs, amt = _validate(coins, amount)
    except CoinChangeError as exc:
        return [str(exc)]
    got = solve(cs, amt)
    errors = []
    # brute force BFS oracle
    INF = amt + 1
    dist = [INF] * (amt + 1)
    dist[0] = 0
    for a in range(1, amt + 1):
        for c in cs:
            if a - c >= 0 and dist[a - c] + 1 < dist[a]:
                dist[a] = dist[a - c] + 1
    oracle = dist[amt] if dist[amt] != INF else -1
    if got != oracle:
        errors.append("answer does not match oracle")
    w = witness(cs, amt)
    if got != -1:
        if sum(w) != amt:
            errors.append("witness does not sum to amount")
        if len(w) != got:
            errors.append("witness length does not match answer")
    else:
        if w:
            errors.append("witness should be empty when impossible")
    return errors
