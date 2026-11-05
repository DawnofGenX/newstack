"""Checks that run without pytest, and that the CLI can run anywhere."""

from __future__ import annotations

import contextlib
import io
import json

from . import cli as cli_module
from . import demo
from .cli import EXIT_BREACH, EXIT_OK, EXIT_UNUSABLE
from .policies import (
    POLICIES,
    Decorrelated,
    EqualJitter,
    Exponential,
    Fixed,
    FullJitter,
    PolicyError,
    by_name,
)
from .rng import MASK, Rng
from .simulate import SimulationError, decreases, delay_series, simulate

ORDER_NAMES = ("fixed", "exponential", "full jitter", "equal jitter", "decorrelated")

CHECKS = 0
FAILED = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global CHECKS, FAILED
    CHECKS += 1
    if condition:
        return
    FAILED += 1
    print(f"FAIL {name}" + (f": {detail}" if detail else ""))


def refuses(name: str, kind, action) -> None:
    try:
        action()
    except kind as error:
        check(name, True)
        check(f"{name} explains itself", len(str(error)) > 10, str(error))
    except Exception as error:
        check(name, False, f"raised {type(error).__name__}: {error}")
    else:
        check(name, False, "nothing was raised")


def quiet(argv: list[str]) -> tuple[int, str]:
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = cli_module.main(argv)
    except SystemExit as exited:
        code = int(exited.code or 0)
    return code, out.getvalue()


def run() -> None:
    first, second = Rng(7), Rng(7)
    check("the generator is deterministic",
          [first.next_u64() for _ in range(3)] == [second.next_u64() for _ in range(3)])
    check("the generator stays inside 64 bits", 0 <= Rng(1).next_u64() <= MASK)
    stream = Rng(9)
    check("random() is in [0, 1)", all(0.0 <= stream.random() < 1.0 for _ in range(500)))
    left, right = Rng(1), Rng(1)
    check("a seed of one draws the same first value as itself",
          left.next_u64() == right.next_u64())
    refuses("a reversed range is refused", ValueError, lambda: Rng(1).uniform(10.0, 1.0))
    refuses("a non-integer seed is refused", TypeError, lambda: Rng(1.5))

    check("fixed returns its own delay",
          Fixed(100.0).delay_ms(Rng(1), 4, 0.0) == 100.0)
    check("exponential doubles by attempt",
          [Exponential(100.0, 2.0, 10_000.0).delay_ms(Rng(1), attempt) for attempt in (1, 2, 3)]
          == [100.0, 200.0, 400.0])
    check("exponential respects the cap",
          Exponential(100.0, 2.0, 1_000.0).delay_ms(Rng(1), 9) == 1_000.0)
    jittered = FullJitter(100.0, 2.0, 1_000.0)
    shared = Rng(3)
    draws = [jittered.delay_ms(shared, attempt) for attempt in range(1, 200)]
    check("full jitter stays under its ceiling",
          all(delay <= jittered.ceiling(attempt) for attempt, delay in enumerate(draws, start=1)),
          str(max(draws)))
    check("full jitter does not return one number",
          len({round(delay, 3) for delay in draws}) > 10)
    equal_rng = Rng(3)
    equal = [EqualJitter(100.0, 2.0, 1_000.0).delay_ms(equal_rng, 1) for _ in range(50)]
    check("equal jitter never goes below half the ceiling",
          all(50.0 <= delay <= 100.0 for delay in equal), str(min(equal)))
    decor = delay_series(Decorrelated(100.0, 1_000.0), seed=4, count=30)
    check("decorrelated is not monotone", decreases(decor) > 0)
    check("decorrelated respects its cap", max(decor) <= 1_000.0, str(max(decor)))
    refuses("a fixed delay of zero is refused", PolicyError, lambda: Fixed(0.0))
    refuses("a shrinking factor is refused", PolicyError, lambda: Exponential(100.0, 0.5))
    refuses("a cap below the base is refused", PolicyError,
            lambda: Decorrelated(1_000.0, 100.0))
    refuses("an unknown policy name is refused", PolicyError, lambda: by_name("magic"))
    check("every policy has a description",
          all(factory().describe() for factory in POLICIES.values()))

    result = simulate(Fixed(100.0), clients=50, seed=7, fail_ms=500.0)
    check("a fixed delay piles every client into one bucket", result.peak_retries == 50,
          str(result.peak_retries))
    check("the pile-up is reported at its own time", result.peak_bucket_ms == 100,
          str(result.peak_bucket_ms))
    check("every client settles", result.completed)
    check("the run reports its attempt count", result.attempts == 50 * 5 + 50, str(result.attempts))
    calm = simulate(FullJitter(100.0, 2.0, 1_000.0), clients=200, seed=7, fail_ms=1_000.0)
    check("full jitter keeps the peak far below the population", calm.peak_retries < 60,
          str(calm.peak_retries))
    check("full jitter uses many buckets", calm.buckets_used > 100, str(calm.buckets_used))
    again = simulate(FullJitter(100.0, 2.0, 1_000.0), clients=200, seed=7, fail_ms=1_000.0)
    check("the same seed gives the same result",
          (calm.peak_retries, calm.retries, calm.done_ms)
          == (again.peak_retries, again.retries, again.done_ms))
    other = simulate(FullJitter(100.0, 2.0, 1_000.0), clients=200, seed=8, fail_ms=1_000.0)
    check("a different seed gives a different curve", other.retries != calm.retries)
    refuses("zero clients is refused", SimulationError, lambda: simulate(Fixed(), clients=0))
    refuses("a zero bucket is refused", SimulationError,
            lambda: simulate(Fixed(), bucket_ms=0.0))
    refuses("no attempts allowed is refused", SimulationError,
            lambda: simulate(Fixed(), max_attempts=0))
    refuses("a negative outage is refused", SimulationError,
            lambda: simulate(Fixed(), fail_ms=-1.0))
    starved = simulate(Exponential(100.0, 2.0, 1_000.0), clients=10, fail_ms=100_000.0,
                       max_attempts=3)
    check("clients that run out of attempts are reported", starved.exhausted == 10,
          str(starved.exhausted))
    check("an exhausted run is not called completed", not starved.completed)

    for story in demo.stories():
        check(f"demo story holds: {story.title}", story.held)
    rendered = demo.render()
    check("the demo prints every story", rendered.count("-> holds") == len(demo.stories()))
    check("the demo does not claim anything broken", "BROKEN" not in rendered)
    check("the demo measures the same outage everywhere", demo.CLIENTS == 200)

    code, out = quiet(["simulate", "--policy", "fixed", "--clients", "30", "--json"])
    check("simulate --json exits zero", code == EXIT_OK, out)
    payload = json.loads(out)
    check("the JSON names the peak", payload["peak_retries"] == 30, out)
    code, out = quiet(["simulate", "--policy", "fixed", "--clients", "30", "--max-peak", "10"])
    check("a breached peak exits one", code == EXIT_BREACH, str(code))
    check("the gate line says BREACH", "BREACH" in out, out)
    code, out = quiet(["simulate", "--policy", "full-jitter", "--clients", "100",
                       "--max-peak", "50"])
    check("a held peak exits zero", code == EXIT_OK, out)
    code, _ = quiet(["simulate", "--policy", "magic"])
    check("an unknown policy exits two", code == EXIT_UNUSABLE, str(code))
    code, out = quiet(["compare", "--clients", "40"])
    check("compare exits zero", code == EXIT_OK, out)
    check("compare prints every policy", all(name in out for name in ORDER_NAMES), out)
    code, out = quiet(["demo"])
    check("the demo command exits zero", code == EXIT_OK, str(code))
    check("the demo command prints story six", "same seed reproduces" in out, out)



def main() -> int:
    run()
    if FAILED:
        print(f"selftest: {FAILED} check(s) failed out of {CHECKS}")
        return 1
    print(f"selftest: {CHECKS} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
