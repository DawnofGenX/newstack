"""A lease is a deadline plus a token; a deadline alone is not a lock."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class LeaseError(ValueError):
    """A request that cannot be granted as asked."""


class Clock(Protocol):
    def now_ms(self) -> int: ...


@dataclass(frozen=True)
class Lease:
    """What a holder believes it owns."""

    holder: str
    token: int
    granted_ms: int
    expires_ms: int

    def text(self) -> str:
        return f"{self.holder:<8} token {self.token:<3} until {self.expires_ms}"

    def valid_at(self, now_ms: int) -> bool:
        return now_ms < self.expires_ms


class LeaseStore:
    """Grants one lease at a time and issues a strictly increasing token with each grant.

    The store's own clock is the authority: a holder's opinion about the time is a hint,
    and a lease that expired in the store is gone no matter what the holder's clock says.

    Renewal extends from *now*, never from the old expiry. Extending from the expiry lets a
    holder that was paused bank the time it did not use, so the lease that "had a second
    left" can outlive its holder by the length of the pause.
    """

    def __init__(self, clock: Clock, ttl_ms: int) -> None:
        if ttl_ms < 1:
            raise LeaseError(f"ttl_ms must be at least 1, got {ttl_ms}")
        self._clock = clock
        self.ttl_ms = ttl_ms
        self._current: Lease | None = None
        self._last_token = 0
        self._grants = 0
        self._renewals = 0
        self._refusals: list[str] = []

    # -- queries --------------------------------------------------------------------
    def now_ms(self) -> int:
        return self._clock.now_ms()

    @property
    def current(self) -> Lease | None:
        return self._current

    def status(self) -> str:
        lease = self._current
        if lease is None:
            return "free"
        if lease.valid_at(self.now_ms()):
            return f"held by {lease.holder} until {lease.expires_ms} (token {lease.token})"
        return f"expired under {lease.holder} at {lease.expires_ms} (token {lease.token})"

    def valid(self, lease: Lease) -> bool:
        current = self._current
        return (
            current is not None
            and current.token == lease.token
            and current.holder == lease.holder
            and lease.valid_at(self.now_ms())
        )

    # -- mutations ------------------------------------------------------------------
    def acquire(self, holder: str) -> Lease | None:
        if not holder:
            raise LeaseError("a lease needs a holder")
        now = self.now_ms()
        if self._current is not None and self._current.valid_at(now):
            self._refusals.append(f"{holder} at {now}: held by {self._current.holder}")
            return None
        self._last_token += 1
        self._grants += 1
        self._current = Lease(holder, self._last_token, now, now + self.ttl_ms)
        return self._current

    def renew(self, lease: Lease) -> Lease | None:
        if not self.valid(lease):
            self._refusals.append(
                f"{lease.holder} at {self.now_ms()}: token {lease.token} is stale"
            )
            return None
        now = self.now_ms()
        self._renewals += 1
        self._current = Lease(lease.holder, lease.token, now, now + self.ttl_ms)
        return self._current

    def release(self, lease: Lease) -> bool:
        if not self.valid(lease):
            self._refusals.append(
                f"{lease.holder} at {self.now_ms()}: cannot release what it holds not"
            )
            return False
        self._current = None
        return True

    # -- reporting ------------------------------------------------------------------
    @property
    def last_token(self) -> int:
        return self._last_token

    @property
    def grants(self) -> int:
        return self._grants

    @property
    def renewals(self) -> int:
        return self._renewals

    @property
    def refusals(self) -> list[str]:
        return list(self._refusals)


def holder_clock_is_irrelevant(store: LeaseStore, lease: Lease, their_now_ms: int) -> bool:
    """A holder believing its lease is alive proves nothing; the store decides."""
    return lease.valid_at(their_now_ms) and not store.valid(lease)
