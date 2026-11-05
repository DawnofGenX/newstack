"""A discrete-event simulation of clients retrying against one recovering server."""

from __future__ import annotations

import heapq
import itertools
from dataclasses import dataclass, field

from .policies import Policy
from .rng import Rng

DEFAULTS = {"clients": 200, "seed": 7, "fail_ms": 1_000.0, "bucket_ms": 10.0,
            "max_attempts": 20}


class SimulationError(ValueError):
    """A simulation whose inputs would make its output meaningless."""


@dataclass(frozen=True)
class Attempt:
    at_ms: float
    client: int
    number: int

    @property
    def is_retry(self) -> bool:
        return self.number > 1


@dataclass
class Result:
    policy: str
    clients: int
    seed: int
    fail_ms: float
    bucket_ms: float
    attempts: int = 0
    retries: int = 0
    exhausted: int = 0
    done_ms: float = 0.0
    peak_retries: int = 0
    peak_bucket_ms: int = 0
    buckets_used: int = 0
    max_delay_ms: float = 0.0
    mean_delay_ms: float = 0.0
    per_bucket: dict[int, int] = field(default_factory=dict)

    @property
    def completed(self) -> bool:
        return self.exhausted == 0

    def lines(self) -> list[str]:
        return [
            f"policy       {self.policy}",
            f"clients      {self.clients} (seed {self.seed}, down until {self.fail_ms:g} ms)",
            f"attempts     {self.attempts} ({self.retries} of them retries)",
            f"peak retries {self.peak_retries} in the {self.bucket_ms:g} ms bucket at "
            f"{self.peak_bucket_ms} ms",
            f"buckets      {self.buckets_used} carried a retry",
            f"delays       mean {self.mean_delay_ms:.1f} ms, longest {self.max_delay_ms:.1f} ms",
            f"settled      {'all clients' if self.completed else f'{self.exhausted} gave up'}"
            f" by {self.done_ms:.0f} ms",
        ]


def simulate(
    policy: Policy,
    *,
    clients: int = 200,
    seed: int = 7,
    fail_ms: float = 1_000.0,
    bucket_ms: float = 10.0,
    max_attempts: int = 20,
) -> Result:
    """Run every client against one server that fails until ``fail_ms``.

    The clock is virtual and the queue is ordered, so the run is exactly
    reproducible: same policy, same seed, same numbers, on every machine.
    """
    if clients < 1:
        raise SimulationError(f"clients must be at least 1, not {clients}")
    if bucket_ms <= 0:
        raise SimulationError(f"bucket_ms must be positive, not {bucket_ms}")
    if max_attempts < 1:
        raise SimulationError(f"max_attempts must be at least 1, not {max_attempts}")
    if fail_ms < 0:
        raise SimulationError(f"fail_ms cannot be negative, not {fail_ms}")

    result = Result(policy=policy.describe(), clients=clients, seed=seed,
                    fail_ms=fail_ms, bucket_ms=bucket_ms)
    rngs = [Rng(seed * 1_000_003 + client) for client in range(clients)]
    previous = [0.0] * clients
    delays: list[float] = []
    queue: list[tuple[float, int, int]] = [(0.0, client, 1) for client in range(clients)]
    heapq.heapify(queue)
    done: list[float] = []

    while queue:
        at_ms, client, number = heapq.heappop(queue)
        result.attempts += 1
        if at_ms >= fail_ms:
            done.append(at_ms)
            continue
        if number >= max_attempts:
            result.exhausted += 1
            continue
        delay = max(0.0, policy.delay_ms(rngs[client], number, previous[client]))
        previous[client] = delay
        delays.append(delay)
        result.retries += 1
        next_at = at_ms + delay
        # Bucket the retry by when it ARRIVES: the pile-up is what the server sees.
        bucket = int(next_at // bucket_ms)
        result.per_bucket[bucket] = result.per_bucket.get(bucket, 0) + 1
        heapq.heappush(queue, (next_at, client, number + 1))

    result.buckets_used = len(result.per_bucket)
    if result.per_bucket:
        peak_bucket, peak = max(result.per_bucket.items(), key=lambda item: (item[1], -item[0]))
        result.peak_retries = peak
        result.peak_bucket_ms = peak_bucket * int(bucket_ms)
    result.done_ms = max(done) if done else 0.0
    if delays:
        result.max_delay_ms = max(delays)
        result.mean_delay_ms = sum(delays) / len(delays)
    return result


def delay_series(policy: Policy, *, seed: int = 7, count: int = 12) -> list[float]:
    """The delays one client would choose in a row, for reading the shape."""
    rng = Rng(seed)
    series: list[float] = []
    previous = 0.0
    for attempt in range(1, count + 1):
        previous = policy.delay_ms(rng, attempt, previous)
        series.append(previous)
    return series


def decreases(series: list[float]) -> int:
    """How often a wait got shorter than the one before it."""
    return sum(1 for earlier, later in itertools.pairwise(series) if later < earlier)
