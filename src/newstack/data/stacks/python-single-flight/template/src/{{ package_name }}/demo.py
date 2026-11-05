"""Four scenarios about stampedes, shown with real threads and a real clock."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from .cache import Answer, SingleFlight
from .model import FlightError


class FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self.value = start

    def now(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


@dataclass(frozen=True)
class Step:
    scenario: str
    lines: list[str]
    ok: bool

    def render(self) -> str:
        verdict = "as advertised" if self.ok else "NOT as advertised"
        body = "".join(f"  {line}\n" for line in self.lines)
        return f"{self.scenario:<40} {verdict}\n{body}"


def _burst(cache: SingleFlight, callers: int) -> tuple[list[Answer], list[BaseException]]:
    answers: list[Answer] = []
    errors: list[BaseException] = []
    lock = threading.Lock()
    start = threading.Barrier(callers + 1)

    def worker() -> None:
        start.wait()
        try:
            answer = cache.get("popular")
        except BaseException as error:
            with lock:
                errors.append(error)
        else:
            with lock:
                answers.append(answer)

    threads = [threading.Thread(target=worker) for _ in range(callers)]
    for thread in threads:
        thread.start()
    start.wait()
    for thread in threads:
        thread.join()
    return answers, errors


def _stampede() -> Step:
    calls = {"n": 0}

    def loader(_key: str) -> str:
        calls["n"] += 1
        time.sleep(0.05)
        return "value"

    cache = SingleFlight(loader)
    started = time.perf_counter()
    answers, errors = _burst(cache, 30)
    elapsed = time.perf_counter() - started
    ok = (
        cache.stats.loads == 1
        and cache.stats.waits == 29
        and cache.stats.failures == 0
        and len(answers) == 30
        and not errors
        and {answer.value for answer in answers} == {"value"}
        and elapsed < 0.5
    )
    return Step(
        "thirty callers, one slow loader",
        [
            f"loader runs: {cache.stats.loads} (calls into the loader: {calls['n']})",
            f"waiters served by the same answer: {len(answers)}",
            f"wall clock: {elapsed * 1000:.0f} ms, not {30 * 50} ms",
            "the eighties stampede cost 30 loads; this costs one",
        ],
        ok,
    )


def _independent() -> Step:
    def loader(key: str) -> str:
        time.sleep(0.3 if key == "slow" else 0.0)
        return f"{key}-value"

    cache = SingleFlight(loader)
    holder: list[object] = []
    thread = threading.Thread(target=lambda: holder.append(cache.get("slow")))
    thread.start()
    time.sleep(0.05)
    started = time.perf_counter()
    fast = cache.get("fast")
    fast_elapsed = time.perf_counter() - started
    thread.join()
    ok = fast_elapsed < 0.15 and fast.value == "fast-value" and fast.hit is False
    return Step(
        "a slow key does not block another",
        [
            f"a different key answered in {fast_elapsed * 1000:.0f} ms while the slow "
            "load was still running",
            f"slow finished as {holder[0].value if holder else '-'}",
            "one registry lock held only long enough to look up a key, not across the load",
        ],
        ok,
    )


def _failure() -> Step:
    attempts = {"n": 0}

    def loader(_key: str) -> str:
        attempts["n"] += 1
        time.sleep(0.02)  # let every caller register as a waiter first
        if attempts["n"] == 1:
            raise ConnectionError("the service is down")
        return "recovered"

    cache = SingleFlight(loader)
    _, errors = _burst(cache, 5)
    messages = {str(error) for error in errors}
    loads_after_burst = cache.stats.loads
    second = cache.get("popular")
    ok = (
        len(errors) == 5
        and len(messages) == 1
        and "the service is down" in messages.pop()
        and loads_after_burst == 1
        and second.value == "recovered"
        and cache.stats.loads == 2
    )
    return Step(
        "a failed load is remembered for nobody",
        [
            f"callers told the same error: {len(errors)} of 5, one distinct message",
            f"loads during the burst: {loads_after_burst}; a negative cache would have "
            "replayed that failure for a whole TTL",
            f"the next call loaded again: {second.value!r}",
        ],
        ok,
    )


def _ttl() -> Step:
    clock = FakeClock()
    cache = SingleFlight(lambda key: f"{key}-{clock.now():.1f}", ttl_s=1.0, clock=clock.now)
    first = cache.get("k")
    clock.advance(0.9)
    during = cache.get("k")
    clock.advance(0.2)
    after = cache.get("k")
    ok = (
        first.hit is False
        and during.hit is True
        and during.value == first.value
        and after.hit is False
        and after.value != first.value
    )
    return Step(
        "a TTL starts when the value became readable",
        [
            f"fresh: {first.value!r}, at 0.9 s: {during.value!r} (a hit), "
            f"at 1.1 s: {after.value!r} (a load)",
            "an entry that a slow loader would have expired before anyone read it is "
            "not a cache, it is a rotation",
        ],
        ok,
    )


SCENARIOS = (_stampede, _independent, _failure, _ttl)


def run() -> list[Step]:
    return [builder() for builder in SCENARIOS]


def render(steps: list[Step]) -> str:
    missed = sum(1 for step in steps if not step.ok)
    body = "\n".join(step.render() for step in steps)
    return f"{body}demo: {len(steps)} scenarios, {missed} not as advertised"


def payload(steps: list[Step]) -> list[dict[str, object]]:
    return [
        {"scenario": step.scenario, "ok": step.ok, "lines": list(step.lines)}
        for step in steps
    ]


def error_of(error: BaseException) -> str:
    """One line about a failure, for a demo that has to print what happened."""
    if isinstance(error, FlightError):
        return f"{error.key}: {type(error.error).__name__}: {error.error}"
    return f"{type(error).__name__}: {error}"
