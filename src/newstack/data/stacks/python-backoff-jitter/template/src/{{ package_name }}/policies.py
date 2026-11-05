"""Five ways to schedule the next attempt, each one a different bet."""

from __future__ import annotations

from .rng import Rng


class PolicyError(ValueError):
    """A policy that cannot answer honestly, rather than one that guesses."""


class Policy:
    """One rule for the delay before the next attempt.

    ``attempt`` is 1-based and counts attempts already made, so ``attempt=1`` is
    the delay after the first failure. ``previous`` is the delay used before this
    one, which only decorrelated jitter reads.
    """

    name = "policy"

    def delay_ms(self, rng: Rng, attempt: int, previous: float = 0.0) -> float:
        raise NotImplementedError

    def describe(self) -> str:
        return self.name


class Fixed(Policy):
    name = "fixed"

    def __init__(self, delay_ms_value: float = 100.0) -> None:
        if delay_ms_value <= 0:
            raise PolicyError(f"a fixed delay must be positive, not {delay_ms_value}")
        self.delay_ms_value = float(delay_ms_value)

    def delay_ms(self, rng: Rng, attempt: int, previous: float = 0.0) -> float:
        return self.delay_ms_value

    def describe(self) -> str:
        return f"fixed {self.delay_ms_value:g} ms"


class Exponential(Policy):
    """base * factor**(attempt - 1), capped.

    A cap is not a detail: without one, attempt 20 at factor 2 is three weeks.
    """

    name = "exponential"

    def __init__(self, base_ms: float = 100.0, factor: float = 2.0,
                 cap_ms: float = 1_000.0) -> None:
        if base_ms <= 0 or cap_ms <= 0:
            raise PolicyError("base and cap must both be positive")
        if factor < 1:
            raise PolicyError(f"a factor below one shortens the wait each time: {factor}")
        self.base_ms = float(base_ms)
        self.factor = float(factor)
        self.cap_ms = float(cap_ms)

    def ceiling(self, attempt: int) -> float:
        return min(self.cap_ms, self.base_ms * (self.factor ** (attempt - 1)))

    def delay_ms(self, rng: Rng, attempt: int, previous: float = 0.0) -> float:
        return self.ceiling(attempt)

    def describe(self) -> str:
        return f"exponential {self.base_ms:g} ms x{self.factor:g} cap {self.cap_ms:g} ms"


class FullJitter(Exponential):
    """A uniform draw between zero and the exponential ceiling."""

    name = "full-jitter"

    def delay_ms(self, rng: Rng, attempt: int, previous: float = 0.0) -> float:
        return rng.uniform(0.0, self.ceiling(attempt))

    def describe(self) -> str:
        return f"full jitter over {self.base_ms:g} ms x{self.factor:g} cap {self.cap_ms:g} ms"


class EqualJitter(Exponential):
    """Half the ceiling plus a uniform draw over the other half."""

    name = "equal-jitter"

    def delay_ms(self, rng: Rng, attempt: int, previous: float = 0.0) -> float:
        half = self.ceiling(attempt) / 2.0
        return half + rng.uniform(0.0, half)

    def describe(self) -> str:
        return f"equal jitter over {self.base_ms:g} ms x{self.factor:g} cap {self.cap_ms:g} ms"


class Decorrelated(Policy):
    """A draw between base and three times the PREVIOUS delay.

    Because it looks at the previous delay rather than the attempt number, the
    sequence is not monotone: it can shorten after a long wait, which is the point
    where this policy stops being a backoff in the textbook sense.
    """

    name = "decorrelated"

    def __init__(self, base_ms: float = 100.0, cap_ms: float = 1_000.0) -> None:
        if base_ms <= 0 or cap_ms <= 0:
            raise PolicyError("base and cap must both be positive")
        if cap_ms < base_ms:
            raise PolicyError(f"a cap of {cap_ms} below the base of {base_ms} can never be met")
        self.base_ms = float(base_ms)
        self.cap_ms = float(cap_ms)

    def delay_ms(self, rng: Rng, attempt: int, previous: float = 0.0) -> float:
        high = previous * 3.0 if previous else self.base_ms * 3.0
        return min(self.cap_ms, rng.uniform(self.base_ms, max(self.base_ms, high)))

    def describe(self) -> str:
        return f"decorrelated {self.base_ms:g} ms cap {self.cap_ms:g} ms"


POLICIES = {
    "fixed": Fixed,
    "exponential": Exponential,
    "full-jitter": FullJitter,
    "equal-jitter": EqualJitter,
    "decorrelated": Decorrelated,
}


def by_name(name: str) -> Policy:
    try:
        factory = POLICIES[name]
    except KeyError as error:
        known = ", ".join(sorted(POLICIES))
        raise PolicyError(f"unknown policy {name!r}; known policies are {known}") from error
    return factory()
