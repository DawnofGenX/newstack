"""Traces whose shape is known before any policy sees them.

Every trace here is generated from a seed, so a hit ratio published in the README is
reproducible on any machine: the shape is a decision (how skewed, how long the loop,
how much of the traffic is a scan), and the numbers follow from it.
"""

from __future__ import annotations

from bisect import bisect_right
from collections import Counter

from .rng import Rng

TRACES = ("zipf", "loop", "scan", "mixed")

DEFAULT_LENGTH = 20_000
DEFAULT_KEYS = 1_000
DEFAULT_SEED = 7


class TraceError(ValueError):
    """A trace that cannot be built as asked."""


def _check(length: int, keys: int) -> None:
    if length < 1:
        raise TraceError(f"a trace needs at least one access, not {length}")
    if keys < 1:
        raise TraceError(f"a trace needs at least one key, not {keys}")


def zipf_trace(
    length: int = DEFAULT_LENGTH,
    keys: int = DEFAULT_KEYS,
    *,
    skew: float = 1.0,
    seed: int = DEFAULT_SEED,
) -> list[str]:
    """Popularity follows 1/rank**skew: a few keys carry most of the traffic."""
    _check(length, keys)
    if skew <= 0:
        raise TraceError(f"a skew must be positive, not {skew}")
    weights = [1.0 / (rank**skew) for rank in range(1, keys + 1)]
    total = sum(weights)
    cumulative: list[float] = []
    running = 0.0
    for weight in weights:
        running += weight / total
        cumulative.append(running)
    rng = Rng(seed)
    return [f"key-{bisect_right(cumulative, rng.random()):05d}" for _ in range(length)]


def loop_trace(
    length: int = DEFAULT_LENGTH, keys: int = 200, *, seed: int = DEFAULT_SEED
) -> list[str]:
    """A fixed set of keys visited in a repeating shuffled order."""
    _check(length, keys)
    order = [f"key-{number:05d}" for number in range(keys)]
    rng = Rng(seed)
    for index in range(keys - 1, 0, -1):
        other = rng.below(index + 1)
        order[index], order[other] = order[other], order[index]
    return [order[number % keys] for number in range(length)]


def scan_trace(
    length: int = DEFAULT_LENGTH,
    hot: int = 50,
    *,
    hot_share: float = 0.5,
    seed: int = DEFAULT_SEED,
) -> list[str]:
    """A working set plus a sequential sweep that will never be reused."""
    _check(length, hot)
    if not 0.0 <= hot_share <= 1.0:
        raise TraceError(f"a hot share is a fraction in 0..1, not {hot_share}")
    rng = Rng(seed)
    keys: list[str] = []
    cold = 0
    for _ in range(length):
        if rng.random() < hot_share:
            keys.append(f"hot-{rng.below(hot):04d}")
        else:
            keys.append(f"scan-{cold:08d}")
            cold += 1
    return keys


def mixed_trace(
    length: int = DEFAULT_LENGTH, keys: int = 500, *, seed: int = DEFAULT_SEED
) -> list[str]:
    """Two thirds zipf popularity, one third a short loop over new keys."""
    _check(length, keys)
    rng = Rng(seed)
    popular = zipf_trace(length, keys, seed=seed)
    repeating = loop_trace(length, max(1, keys // 5), seed=seed + 1)
    loop = [f"loop-{key}" for key in repeating]
    keys_out: list[str] = []
    for position in range(length):
        if rng.random() < 0.66:
            keys_out.append(popular[position])
        else:
            keys_out.append(loop[position])
    return keys_out


def build(name: str, length: int = DEFAULT_LENGTH, *, seed: int = DEFAULT_SEED) -> list[str]:
    """The named trace, at the length asked for."""
    if name == "zipf":
        return zipf_trace(length, seed=seed)
    if name == "loop":
        return loop_trace(length, seed=seed)
    if name == "scan":
        return scan_trace(length, seed=seed)
    if name == "mixed":
        return mixed_trace(length, seed=seed)
    raise TraceError(f"unknown trace {name!r}; known traces are {', '.join(TRACES)}")


def frequency(trace: list[str]) -> Counter[str]:
    """How often each key appears - the shape the ceiling is computed from."""
    return Counter(trace)


def describe(name: str) -> str:
    """One sentence per trace, so a table can say what it measured."""
    lines = {
        "zipf": "1/rank popularity over 1000 keys, so a few keys carry most of the traffic",
        "loop": "a shuffled cycle over 200 keys repeated, which is the classic LRU worst case",
        "scan": "half a hot working set, half a sequential sweep that is never reused",
        "mixed": "two thirds popularity over 500 keys, one third a loop over 100 keys",
    }
    try:
        return lines[name]
    except KeyError:
        raise TraceError(f"unknown trace {name!r}; known traces are {', '.join(TRACES)}") from None
