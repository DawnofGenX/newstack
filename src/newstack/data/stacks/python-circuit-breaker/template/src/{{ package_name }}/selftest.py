"""The built-in checks: run them with `selftest`, no pytest required.

Every check below is a claim the README makes, so a reader can see the claim and its proof
in the same file.
"""

from __future__ import annotations

from collections.abc import Callable

from . import demo
from .breaker import Breaker
from .clock import FakeClock, Monotonic
from .model import OpenError, State


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


def _gate_checks(checks: Checks) -> None:
    clock = FakeClock()
    breaker = Breaker(failure_threshold=3, cooldown_s=30.0, clock=clock)
    checks.equal("a closed breaker allows", True, breaker.allow().allowed)

    for _ in range(2):
        breaker.record_success()
    for _ in range(2):
        breaker.record_failure()
    checks.equal("two failures of three keep it closed", State.CLOSED, breaker.state)
    checks.equal("and the count is two", 2, breaker.consecutive_failures)

    breaker.record_success()
    checks.equal("a success resets the count", 0, breaker.consecutive_failures)

    for _ in range(3):
        breaker.record_failure()
    checks.equal("three in a row open it", State.OPEN, breaker.state)
    checks.equal("the trip is counted", 1, breaker.tally.trips)

    denied = breaker.allow()
    checks.equal("an open breaker denies", False, denied.allowed)
    checks.equal("and says how long", 30.0, denied.retry_in)

    clock.advance(10)
    checks.equal("ten seconds later it still denies", False, breaker.allow().allowed)
    checks.equal("with the remaining time", 20.0, breaker.retry_in())

    clock.advance(20)
    probe = breaker.allow()
    checks.equal("the cooldown over grants one probe", True, probe.allowed)
    checks.equal("in the half-open state", State.HALF_OPEN, breaker.state)
    second = breaker.allow()
    checks.equal("a second caller is refused while the probe runs", False, second.allowed)
    checks.equal("for the reason it says", "half-open, a probe is already in flight", second.reason)

    breaker.record_success()
    checks.equal("a successful probe closes it", State.CLOSED, breaker.state)
    checks.equal("and there was one probe", 1, breaker.tally.probes)


def _probe_checks(checks: Checks) -> None:
    clock = FakeClock()
    breaker = Breaker(failure_threshold=1, cooldown_s=10.0, clock=clock)
    breaker.record_failure()
    clock.advance(10)
    breaker.allow()
    breaker.record_failure()
    checks.equal("a failed probe re-opens it", State.OPEN, breaker.state)
    checks.equal("and restarts the cooldown", 10.0, breaker.retry_in())
    checks.equal("with two trips counted", 2, breaker.tally.trips)

    clock = FakeClock()
    patient = Breaker(failure_threshold=1, cooldown_s=5.0, half_open_successes=2, clock=clock)
    patient.record_failure()
    clock.advance(5)
    checks.equal("two successes needed: first probe", True, patient.allow().allowed)
    patient.record_success()
    checks.equal("one success is not enough to close", State.HALF_OPEN, patient.state)
    checks.equal("so the next probe is admitted", True, patient.allow().allowed)
    patient.record_success()
    checks.equal("the second one closes it", State.CLOSED, patient.state)


def _classification_checks(checks: Checks) -> None:
    clock = FakeClock()
    breaker = Breaker(failure_threshold=1, cooldown_s=10.0, clock=clock, ignore=(ValueError,))
    counted = breaker.record_failure(ValueError("bad request"))
    checks.equal("an ignored error does not count", False, counted)
    checks.equal("and leaves the breaker closed", State.CLOSED, breaker.state)
    checks.equal("but is tallied", 1, breaker.tally.ignored)
    checks.equal("an unclassified error counts", True, breaker.record_failure(RuntimeError("503")))
    checks.equal("and trips it", State.OPEN, breaker.state)
    breaker.record_failure(RuntimeError("slow 503 from before the trip"))
    checks.equal("a straggler failure while open is late", 1, breaker.tally.late)
    checks.equal("a straggler does not extend the cooldown", 10.0, breaker.retry_in())
    checks.equal("and does not trip again", 1, breaker.tally.trips)

    clock = FakeClock()
    half = Breaker(failure_threshold=1, cooldown_s=1.0, clock=clock, ignore=(ValueError,))
    half.record_failure()
    clock.advance(1)
    half.allow()
    half.record_failure(ValueError("422"))
    checks.equal("an ignored probe failure releases the probe", State.HALF_OPEN, half.state)
    checks.equal("so another probe is admitted", True, half.allow().allowed)


def _call_checks(checks: Checks) -> None:
    clock = FakeClock()
    breaker = Breaker(failure_threshold=1, cooldown_s=5.0, clock=clock)
    checks.equal("call returns the value", 42, breaker.call(lambda: 42))
    checks.equal("and records a success", 1, breaker.tally.successes)

    def explode() -> None:
        raise RuntimeError("down")

    try:
        breaker.call(explode)
    except RuntimeError:
        checks.ok("call re-raises the original error", True)
    else:
        checks.ok("call re-raises the original error", False)
    checks.equal("and records the failure", State.OPEN, breaker.state)

    try:
        breaker.call(lambda: 1)
    except OpenError as refused:
        checks.equal("call refuses while open", True, True)
        checks.equal("with the retry time attached", 5.0, refused.retry_in)
    else:
        checks.ok("call refuses while open", False)

    checks.equal("a refused call is denied, not failed", 1, breaker.tally.failures)


def _validation_checks(checks: Checks) -> None:
    checks.raises(
        "a threshold of zero is refused",
        ValueError,
        lambda: Breaker(failure_threshold=0),
    )
    checks.raises(
        "a negative cooldown is refused",
        ValueError,
        lambda: Breaker(cooldown_s=-1.0),
    )
    checks.raises(
        "zero half-open successes is refused",
        ValueError,
        lambda: Breaker(half_open_successes=0),
    )
    clock = FakeClock()
    checks.raises(
        "a fake clock cannot run backwards",
        ValueError,
        lambda: clock.advance(-1),
    )
    real = Monotonic()
    checks.ok("the monotonic clock only moves forward", real.now() > 0)

    breaker = Breaker(clock=FakeClock())
    breaker.record_failure()
    breaker.reset()
    checks.equal("reset closes it", State.CLOSED, breaker.state)
    checks.equal("without erasing the counters", 1, breaker.tally.failures)


def _demo_checks(checks: Checks) -> None:
    timeline = demo.run()
    checks.equal("the demo reproduces its own timeline", True, timeline.ok)
    checks.equal("it ends closed", State.CLOSED, timeline.steps[-1].state)
    checks.ok("the refusal is on the timeline", any("deny" in line for line in timeline.lines()))
    checks.ok(
        "so is the probe",
        any("half-open, single probe" in line for line in timeline.lines()),
    )
    checks.ok("time is printed", timeline.lines()[0].startswith("t="))
    checks.raises("a demo without failures is refused", ValueError, lambda: demo.run(failures=0))


def run() -> int:
    checks = Checks()
    for group in (
        _gate_checks,
        _probe_checks,
        _classification_checks,
        _call_checks,
        _validation_checks,
        _demo_checks,
    ):
        group(checks)
    total = checks.passed + checks.failed
    print(f"\nselftest: {checks.passed} checks passed, {checks.failed} failed out of {total}")
    return 0 if checks.failed == 0 else 1
