"""The state machine itself.

The rules, in the order they matter:

1. **Closed** counts *consecutive* failures. One success puts the count back to zero: a
   windowed count is a different, defensible design, but it lets five failures from ten
   minutes ago trip the breaker for a service that has answered a thousand times since.
2. Five in a row opens the breaker and starts the cooldown.
3. While open, every caller is refused *without* a network call, and `retry_in` says when
   that changes.
4. After the cooldown the breaker admits **exactly one** probe. One, not "a few": the point
   of the probe is to find out whether the dependency is back, and twenty probes is how you
   finish off a service that was just coming up.
5. A failed probe re-opens the breaker and restarts the cooldown from that moment, so a
   dependency that is still down is retried every `cooldown_s`, not every request.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from .clock import Clock, Monotonic
from .model import Decision, OpenError, State, Tally

DEFAULT_FAILURE_THRESHOLD = 5
DEFAULT_COOLDOWN_S = 30.0
DEFAULT_HALF_OPEN_SUCCESSES = 1


class Breaker:
    """A circuit breaker with a caller-supplied clock and an explicit failure classifier."""

    def __init__(
        self,
        *,
        failure_threshold: int = DEFAULT_FAILURE_THRESHOLD,
        cooldown_s: float = DEFAULT_COOLDOWN_S,
        half_open_successes: int = DEFAULT_HALF_OPEN_SUCCESSES,
        clock: Clock | None = None,
        ignore: Iterable[type[BaseException]] = (),
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be at least 1")
        if cooldown_s < 0:
            raise ValueError("cooldown_s cannot be negative")
        if half_open_successes < 1:
            raise ValueError("half_open_successes must be at least 1")
        self.failure_threshold = failure_threshold
        self.cooldown_s = float(cooldown_s)
        self.half_open_successes = half_open_successes
        self.clock = clock or Monotonic()
        self.ignore = tuple(ignore)
        self.tally = Tally()
        self._state = State.CLOSED
        self._consecutive_failures = 0
        self._opened_at = 0.0
        self._probe_in_flight = False
        self._probe_successes = 0

    # --- observation -----------------------------------------------------------------

    @property
    def state(self) -> State:
        return self._state

    @property
    def consecutive_failures(self) -> int:
        return self._consecutive_failures

    def stats(self) -> dict[str, int]:
        return {**self.tally.as_dict(), "consecutive_failures": self._consecutive_failures}

    def retry_in(self) -> float:
        """Seconds until a probe is allowed; zero unless the breaker is open."""
        if self._state is not State.OPEN:
            return 0.0
        remaining = self.cooldown_s - (self.clock.now() - self._opened_at)
        return round(max(0.0, remaining), 6)

    # --- the gate --------------------------------------------------------------------

    def allow(self) -> Decision:
        """Answer yes or no, changing state when the clock says the cooldown is over."""
        self.tally.requests += 1
        if self._state is State.CLOSED:
            return self._grant(self._closed_decision())
        if self._state is State.OPEN:
            remaining = self.retry_in()
            if remaining > 0:
                return self._refuse(
                    Decision(
                        allowed=False,
                        state=State.OPEN,
                        reason=f"open, next probe in {remaining:.1f}s",
                        retry_in=remaining,
                    )
                )
            self._state = State.HALF_OPEN
            self._probe_successes = 0
            return self._grant(self._probe_decision())
        return self._half_open_decision()

    def record_success(self) -> None:
        """A request that was allowed came back healthy."""
        self.tally.successes += 1
        if self._state is State.CLOSED:
            self._consecutive_failures = 0
        elif self._state is State.HALF_OPEN:
            self._probe_in_flight = False
            self._probe_successes += 1
            if self._probe_successes >= self.half_open_successes:
                self._close()
        else:
            self._late()

    def record_failure(self, error: BaseException | None = None) -> bool:
        """A request that was allowed failed; returns whether it counted against the breaker.

        An exception listed in `ignore` is a *caller* error, not an outage: a 404 or a
        validation error says the dependency is perfectly healthy and the request was wrong.
        Such an error still releases the probe it occupied, otherwise one ignored failure in
        the half-open state would hold the breaker shut forever.
        """
        if error is not None and self.ignore and isinstance(error, self.ignore):
            self.tally.ignored += 1
            if self._state is State.HALF_OPEN:
                self._probe_in_flight = False
            return False
        self.tally.failures += 1
        if self._state is State.CLOSED:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self.failure_threshold:
                self._open()
        elif self._state is State.HALF_OPEN:
            self._probe_in_flight = False
            self._open()
        else:
            self._late()
        return True

    def call(self, function: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Run `function` under the breaker: refuse when open, record what came back."""
        decision = self.allow()
        if not decision.allowed:
            raise OpenError(decision)
        try:
            result = function(*args, **kwargs)
        except BaseException as error:
            self.record_failure(error)
            raise
        self.record_success()
        return result

    def reset(self) -> None:
        """Put the breaker back to closed without touching the counters."""
        self._state = State.CLOSED
        self._consecutive_failures = 0
        self._probe_in_flight = False
        self._probe_successes = 0

    # --- internals -------------------------------------------------------------------

    def _grant(self, decision: Decision) -> Decision:
        self.tally.allowed += 1
        return decision

    def _refuse(self, decision: Decision) -> Decision:
        self.tally.denied += 1
        return decision

    def _late(self) -> None:
        # A request that started before the trip finishes after it. Letting that result move
        # the breaker is how a single straggler keeps a recovered dependency shut.
        self.tally.late += 1

    def _closed_decision(self) -> Decision:
        return Decision(allowed=True, state=State.CLOSED, reason="closed")

    def _probe_decision(self) -> Decision:
        self._probe_in_flight = True
        self.tally.probes += 1
        return Decision(allowed=True, state=State.HALF_OPEN, reason="half-open, single probe")

    def _half_open_decision(self) -> Decision:
        if self._probe_in_flight:
            return self._refuse(
                Decision(
                    allowed=False,
                    state=State.HALF_OPEN,
                    reason="half-open, a probe is already in flight",
                )
            )
        return self._grant(self._probe_decision())

    def _open(self) -> None:
        self._state = State.OPEN
        self._opened_at = self.clock.now()
        self._probe_in_flight = False
        self._probe_successes = 0
        self.tally.trips += 1

    def _close(self) -> None:
        self._state = State.CLOSED
        self._consecutive_failures = 0
        self._probe_in_flight = False
        self._probe_successes = 0
