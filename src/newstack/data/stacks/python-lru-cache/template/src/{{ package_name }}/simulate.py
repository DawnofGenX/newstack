"""Run policies over one trace and report what each of them bought."""

from __future__ import annotations

from dataclasses import dataclass

from .cache import POLICIES, Cache, by_name
from .trace import frequency


class SimulationError(ValueError):
    """A comparison that cannot be made."""


@dataclass(frozen=True)
class Metrics:
    """One policy's result on one trace."""

    policy: str
    capacity: int
    accesses: int
    hits: int
    misses: int
    evictions: int
    scan_work: int
    promotions: int
    hit_rate: float

    def line(self) -> str:
        return (
            f"{self.policy:<6} {self.capacity:>8} {self.hit_rate:>10.4f} {self.hits:>8} "
            f"{self.evictions:>9} {self.scan_work:>8} {self.promotions:>10}"
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "policy": self.policy,
            "capacity": self.capacity,
            "accesses": self.accesses,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "scan_work": self.scan_work,
            "promotions": self.promotions,
            "hit_rate": self.hit_rate,
        }


def run(policy: str, trace: list[str], capacity: int) -> Metrics:
    """Feed the trace through one policy and collect its counters."""
    if not trace:
        raise SimulationError("a trace holds no accesses")
    chosen: type[Cache] = by_name(policy)
    cache = chosen(capacity)
    for key in trace:
        cache.access(key)
    return Metrics(
        policy=cache.name,
        capacity=capacity,
        accesses=cache.accesses,
        hits=cache.hits,
        misses=cache.misses,
        evictions=cache.evictions,
        scan_work=cache.scans,
        promotions=cache.promotions,
        hit_rate=cache.hit_rate,
    )


def compare(trace: list[str], capacity: int) -> list[Metrics]:
    """Every policy, in a fixed order, on the same trace."""
    return [run(name, trace, capacity) for name in POLICIES]


def ceiling(trace: list[str], capacity: int) -> float:
    """The ceiling no policy can beat: the share of accesses to the top `capacity` keys."""
    if not trace:
        raise SimulationError("a trace holds no accesses")
    if capacity < 1:
        raise SimulationError(f"a capacity needs to be at least 1, not {capacity}")
    counts = frequency(trace).most_common(capacity)
    return sum(count for _, count in counts) / len(trace)


def capacity_curve(trace: list[str], capacities: list[int], policy: str = "lru") -> list[Metrics]:
    """The same policy at several capacities, which is what a sizing decision needs."""
    if not capacities:
        raise SimulationError("a curve needs at least one capacity")
    for capacity in capacities:
        if capacity < 1:
            raise SimulationError(f"a capacity needs to be at least 1, not {capacity}")
    return [run(policy, trace, capacity) for capacity in capacities]


def winner(results: list[Metrics]) -> Metrics:
    """The best hit ratio, with the first policy winning a tie (order is fixed)."""
    if not results:
        raise SimulationError("there is nothing to compare")
    best = results[0]
    for result in results[1:]:
        if result.hit_rate > best.hit_rate:
            best = result
    return best


def header() -> str:
    """The column header the rows in `Metrics.line` line up with."""
    return (
        f"{'policy':<6} {'capacity':>8} {'hit rate':>10} {'hits':>8} "
        f"{'evictions':>9} {'scans':>8} {'promotions':>10}"
    )
