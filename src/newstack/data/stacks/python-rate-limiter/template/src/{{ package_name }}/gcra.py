"""GCRA: one integer per key, no floats, no drift, and the Retry-After is derived.

The generic cell rate algorithm keeps a single number per key — the theoretical arrival time of
the next request it would admit, `tat`. A request at time `t` is allowed when

    max(tat, t) + (cost - 1) * interval - tolerance <= t

and when it is allowed, `tat` becomes `max(tat, t) + cost * interval`. `tolerance` is
`(burst - 1) * interval`, so a full bucket admits `burst` requests at once and then one per
interval.

Everything is an integer count of microseconds multiplied by `limit`, which makes the interval
`per_seconds * 1_000_000` exactly. A float token bucket adds `rate * elapsed` and loses a
little every time; after a million requests the leak is visible, and no test finds it because
each step looks fine.
"""

from __future__ import annotations

from .model import MICROSECONDS, Config, Decision


def _ceil_div(value: int, divisor: int) -> int:
    return -(-value // divisor)


class Gcra:
    """One key's state: `tat`, in units of microseconds * limit."""

    __slots__ = ("_tat", "config", "interval", "tolerance")

    def __init__(self, config: Config, now_us: int) -> None:
        self.config = config
        self.interval = config.per_seconds * MICROSECONDS
        self.tolerance = (config.burst - 1) * self.interval
        self._tat = now_us * config.limit

    @property
    def tat_us(self) -> int:
        """When this key would next admit a request, in microseconds."""
        return _ceil_div(self._tat - self.tolerance, self.config.limit)

    @property
    def full_at_us(self) -> int:
        """When the bucket is completely refilled, in microseconds."""
        return _ceil_div(self._tat, self.config.limit)

    def check(self, key: str, now_us: int, cost: int = 1) -> Decision:
        if isinstance(cost, bool) or not isinstance(cost, int):
            raise ValueError(f"cost must be an integer, got {cost!r}")
        if cost < 1:
            raise ValueError(f"cost must be at least 1, got {cost}")
        if cost > self.config.burst:
            raise ValueError(
                f"cost {cost} exceeds the burst {self.config.burst}: a request that can never be "
                "admitted is a configuration error, not a denial"
            )
        limit = self.config.limit
        now = now_us * limit
        tat = max(self._tat, now)

        # The earliest instant this request may leave: the stored arrival time, pushed forward
        # by the cost it needs, minus the burst tolerance it is allowed to spend.
        earliest = tat + (cost - 1) * self.interval - self.tolerance
        if earliest > now:
            return Decision(
                allowed=False,
                key=key,
                remaining=max(0, (now + self.tolerance - tat) // self.interval + 1),
                retry_after_us=_ceil_div(earliest - now, limit),
                reset_at_us=_ceil_div(tat, limit),
                cost=cost,
            )

        self._tat = tat + cost * self.interval
        return Decision(
            allowed=True,
            key=key,
            remaining=max(0, (now + self.tolerance - self._tat) // self.interval + 1),
            retry_after_us=0,
            reset_at_us=_ceil_div(self._tat, limit),
            cost=cost,
        )

    def idle(self, now_us: int) -> bool:
        """True once the bucket is full: the next check behaves exactly as on a fresh key."""
        return self._tat <= now_us * self.config.limit

    def forget(self) -> None:
        """Reset the key's state: the bucket is full again as of the next check."""
        self._tat = 0
