"""Every claim the README makes, checked against the same integer arithmetic."""

from __future__ import annotations

import threading
from collections.abc import Callable

from .clock import FakeClock
from .gcra import Gcra
from .limiter import Limiter
from .model import Config, Decision


class Checks:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def ok(self, name: str, condition: bool) -> None:
        if condition:
            self.passed += 1
            print(f"ok   {name}")
        else:
            self.failed += 1
            print(f"FAIL {name}")

    def equal(self, name: str, want: object, got: object) -> None:
        self.ok(f"{name} (want {want!r}, got {got!r})", want == got)

    def raises(self, name: str, error: type[BaseException], action: Callable[[], object]) -> None:
        try:
            action()
        except error:
            self.ok(name, True)
        except BaseException as unexpected:
            self.ok(f"{name} (raised {type(unexpected).__name__} instead)", False)
        else:
            self.ok(f"{name} (nothing was raised)", False)


def _config_checks(checks: Checks) -> None:
    checks.raises("a zero limit is refused", ValueError, lambda: Config(limit=0))
    checks.raises("a zero window is refused", ValueError, lambda: Config(per_seconds=0))
    checks.raises("a zero capacity is refused", ValueError, lambda: Config(capacity=0))
    checks.raises("a boolean limit is refused", ValueError, lambda: Config(limit=True))
    checks.equal("the burst defaults to the limit", 100, Config().burst)
    checks.equal("and can be set on its own", 7, Config(limit=100, capacity=7).burst)


def _burst_checks(checks: Checks) -> None:
    clock = FakeClock()
    state = Gcra(Config(limit=2, per_seconds=1, capacity=3), clock.now_us())
    decisions = [state.check("k", clock.now_us()) for _ in range(4)]
    checks.equal(
        "a burst of three is allowed",
        [True, True, True, False],
        [decision.allowed for decision in decisions],
    )
    checks.equal(
        "remaining counts the bucket down",
        [2, 1, 0, 0],
        [decision.remaining for decision in decisions],
    )
    denied = decisions[3]
    checks.equal("the fourth request is told to wait one interval", 500_000, denied.retry_after_us)
    checks.equal("a denial says when the bucket is full again", 1_500_000, denied.reset_at_us)
    clock.advance_s(0.5)
    later = state.check("k", clock.now_us()).allowed
    checks.ok("half an interval later the key is allowed again", later)
    clock.advance_s(0.5)
    checks.ok("and once more an interval after that", state.check("k", clock.now_us()).allowed)
    checks.ok("but not again in the same instant", not state.check("k", clock.now_us()).allowed)


def _cost_checks(checks: Checks) -> None:
    clock = FakeClock()
    state = Gcra(Config(limit=1, per_seconds=1, capacity=3), clock.now_us())

    def spend(cost: int) -> Decision:
        return state.check("k", clock.now_us(), cost=cost)

    checks.ok("a cost of two fits in a burst of three", spend(2).allowed)
    checks.equal("then a cost of one leaves nothing", 0, spend(1).remaining)
    checks.raises("a cost above the burst is a configuration error", ValueError, lambda: spend(4))
    checks.raises("a zero cost is refused", ValueError, lambda: spend(0))
    checks.raises("a boolean cost is refused", ValueError, lambda: spend(True))


def _idle_checks(checks: Checks) -> None:
    clock = FakeClock()
    state = Gcra(Config(limit=2, per_seconds=1, capacity=3), clock.now_us())
    for _ in range(3):
        state.check("k", clock.now_us())
    checks.ok("a spent key is not idle", not state.idle(clock.now_us()))
    clock.advance_s(1.0)
    checks.ok("and still not idle while tokens are missing", not state.idle(clock.now_us()))
    clock.advance_s(0.5)
    checks.ok("once the bucket is full again it is idle", state.idle(clock.now_us()))


def _limiter_checks(checks: Checks) -> None:
    clock = FakeClock()
    limiter = Limiter(Config(limit=2, per_seconds=1, capacity=2), clock)
    checks.ok("key a is allowed", limiter.check("a").allowed)
    checks.ok("key a again is allowed", limiter.check("a").allowed)
    checks.ok("key a a third time is denied", not limiter.check("a").allowed)
    checks.ok("key b is untouched by key a", limiter.check("b").allowed)
    checks.equal("two keys are tracked", 2, len(limiter))
    checks.equal("no wait is needed for a fresh key", 0, limiter.wait_time_us("c"))
    checks.equal("a fresh key is not created by asking", 2, len(limiter))
    checks.equal("waiting does not spend", 500_000, limiter.wait_time_us("a"))
    clock.advance_s(1.0)
    checks.equal("an idle key is pruned", 2, limiter.prune())
    checks.equal("and forgotten", 0, len(limiter))
    stats = limiter.stats()
    checks.equal("the counters add up", stats["checks"], stats["allowed"] + stats["denied"])
    checks.equal("the eviction is counted", 2, stats["evicted"])
    checks.raises("an empty key is refused", ValueError, lambda: limiter.check(""))


def _bounded_keys_checks(checks: Checks) -> None:
    limiter = Limiter(Config(limit=10, per_seconds=1, capacity=10), FakeClock(), max_keys=3)
    for index in range(20):
        limiter.check(f"user-{index}")
    checks.equal("the table never grows past max_keys", 3, len(limiter))
    checks.ok("and the evictions are reported", limiter.stats()["evicted"] > 0)
    checks.raises("max_keys below one is refused", ValueError, lambda: Limiter(max_keys=0))
    checks.raises("prune_every below one is refused", ValueError, lambda: Limiter(prune_every=0))


def _thread_checks(checks: Checks) -> None:
    limiter = Limiter(Config(limit=10, per_seconds=1, capacity=10), FakeClock())
    allowed = []
    lock = threading.Lock()

    def worker() -> None:
        for _ in range(50):
            decision = limiter.check("shared")
            if decision.allowed:
                with lock:
                    allowed.append(decision.cost)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    checks.equal("eight threads spend a bucket of ten exactly once", 10, len(allowed))


def _invariant_checks(checks: Checks) -> None:
    """The claim a reviewer cares about: no window ever admits more than its share."""
    limit, per_seconds, burst = 5, 1, 5
    interval_us = per_seconds * 1_000_000 // limit
    clock = FakeClock()
    limiter = Limiter(Config(limit=limit, per_seconds=per_seconds, capacity=burst), clock)
    stamps: list[int] = []
    for _ in range(400):
        clock.advance(37_000)
        if limiter.check("k").allowed:
            stamps.append(clock.now_us())
    worst = 0
    for index, start in enumerate(stamps):
        window = sum(1 for stamp in stamps[index:] if stamp - start < 1_000_000)
        worst = max(worst, window)
    ceiling = burst + limit  # a burst plus one second of refill
    checks.ok(f"no one-second window admits more than {ceiling} ({worst})", worst <= ceiling)
    checks.ok("and the limiter did admit something", len(stamps) > 0)
    expected = 400 * 37_000 // interval_us
    checks.ok(
        f"the admitted count tracks the rate ({len(stamps)} vs about {expected})",
        abs(len(stamps) - expected) <= burst,
    )


def run() -> int:
    checks = Checks()
    groups = (
        _config_checks,
        _burst_checks,
        _cost_checks,
        _idle_checks,
        _limiter_checks,
        _bounded_keys_checks,
        _thread_checks,
        _invariant_checks,
    )
    for group in groups:
        group(checks)
    total = checks.passed + checks.failed
    print(f"\nselftest: {checks.passed} checks passed, {checks.failed} failed out of {total}")
    return 0 if checks.failed == 0 else 1
