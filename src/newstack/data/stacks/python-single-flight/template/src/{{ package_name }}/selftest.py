"""Checks the cache without pytest, threads included."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

from . import demo
from .cache import SingleFlight
from .model import FlightError, LoadError


class Checks:
    def __init__(self) -> None:
        self.passed = 0
        self.total = 0

    def ok(self, description: str, condition: bool) -> None:
        self.total += 1
        if condition:
            self.passed += 1
        else:
            print(f"FAIL  {description}")

    def equal(self, description: str, want: object, got: object) -> None:
        self.ok(f"{description} (want {want!r}, got {got!r})", want == got)

    def raises(
        self,
        description: str,
        function: Callable[..., object],
        *args: object,
        **kwargs: object,
    ) -> None:
        try:
            function(*args, **kwargs)
        except (LoadError, FlightError, ValueError, TypeError):
            self.ok(description, True)
        else:
            self.ok(f"{description} (nothing was raised)", False)


class Clock:
    def __init__(self, start: float = 0.0) -> None:
        self.value = start

    def now(self) -> float:
        return self.value


def _cache(loader: Callable[[str], object], **kwargs: object) -> SingleFlight:
    return SingleFlight(loader, **kwargs)  # type: ignore[arg-type]


def _model_checks(checks: Checks) -> None:
    checks.raises("an empty key is refused", _cache(lambda key: key).get, "")
    typed = _cache(lambda key: key)
    checks.raises("a non-string key is refused", typed.get, 3)  # type: ignore[arg-type]
    checks.raises("a zero ttl is refused", _cache, lambda key: key, ttl_s=0)
    checks.raises("a negative ttl is refused", _cache, lambda key: key, ttl_s=-1)
    checks.raises("a non-callable loader is refused", SingleFlight, 3)  # type: ignore[arg-type]
    cache = _cache(lambda key: key.upper())
    checks.equal("a miss loads", cache.get("a").value, "A")
    checks.equal("the second call is a hit", cache.get("a").hit, True)
    checks.equal("a hit does not load", cache.stats.loads, 1)
    checks.equal("peek does not load", cache.peek("never"), None)
    checks.equal("peek sees a loaded value", cache.peek("a").value, "A")  # type: ignore[union-attr]
    checks.equal("forget drops the entry", cache.forget("a"), True)
    checks.equal("forget on a missing key is false", cache.forget("a"), False)
    checks.equal("len counts entries", len(cache), 0)


def _thread_checks(checks: Checks) -> None:
    calls = {"n": 0}

    def loader(key: str) -> str:
        calls["n"] += 1
        time.sleep(0.05)
        return f"{key}-value"

    cache = _cache(loader)
    answers: list[object] = []
    gate = threading.Barrier(21)
    lock = threading.Lock()

    def worker() -> None:
        gate.wait()
        answer = cache.get("k")
        with lock:
            answers.append(answer.value)

    threads = [threading.Thread(target=worker) for _ in range(20)]
    for thread in threads:
        thread.start()
    gate.wait()
    for thread in threads:
        thread.join()
    checks.equal("twenty callers run the loader once", calls["n"], 1)
    checks.equal("one loader run, nineteen waiters", cache.stats.waits, 19)
    checks.equal("everybody got the same value", len(set(answers)), 1)

    slow = _cache(lambda key: time.sleep(0.3) if key == "slow" else "fast-value")
    thread = threading.Thread(target=lambda: slow.get("slow"))
    thread.start()
    time.sleep(0.05)
    started = time.perf_counter()
    fast = slow.get("fast")
    elapsed = time.perf_counter() - started
    thread.join()
    checks.equal("a second key is not behind the first", fast.value, "fast-value")
    checks.ok("a second key does not wait for the slow load", elapsed < 0.15)


def _failure_checks(checks: Checks) -> None:
    attempts = {"n": 0}

    def loader(_key: str) -> str:
        attempts["n"] += 1
        time.sleep(0.02)
        if attempts["n"] == 1:
            raise ConnectionError("down")
        return "recovered"

    cache = _cache(loader)
    errors: list[BaseException] = []
    gate = threading.Barrier(5)
    lock = threading.Lock()

    def worker() -> None:
        gate.wait()
        try:
            cache.get("k")
        except BaseException as error:
            with lock:
                errors.append(error)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for thread in threads:
        thread.start()
    gate.wait()
    for thread in threads:
        thread.join()
    checks.equal("every waiter heard about the failure", len(errors), 4)
    checks.ok("the failure names the key", all(isinstance(error, FlightError) for error in errors))
    checks.equal("a failure is one load, not one per caller", cache.stats.loads, 1)
    checks.equal("the next call loads again", cache.get("k").value, "recovered")
    checks.equal("no negative cache was kept", cache.stats.loads, 2)

    def always_fails(_key: str) -> str:
        raise RuntimeError("nope")

    broken = _cache(always_fails)
    checks.raises("the loader's error reaches the caller", broken.get, "k")
    checks.raises("a failure does not stay in the cache", broken.get, "k")
    checks.equal("each attempt was a load", broken.stats.loads, 2)
    checks.equal("failures are counted", broken.stats.failures, 2)
    checks.equal("a failed key is not in the cache", len(broken), 0)


def _ttl_checks(checks: Checks) -> None:
    clock = Clock()
    cache = _cache(lambda key: f"{key}-{clock.now():.1f}", ttl_s=1.0, clock=clock.now)
    first = cache.get("k")
    clock.value = 0.99
    during = cache.get("k")
    clock.value = 1.0
    after = cache.get("k")
    checks.equal("a fresh entry is a miss", first.hit, False)
    checks.equal("an entry inside its ttl is a hit", during.hit, True)
    checks.equal("the ttl boundary expires the entry", after.hit, False)
    checks.ok("the expired entry was replaced", after.value != first.value)
    forever = _cache(lambda key: key)
    forever.get("k")
    checks.ok("a cache without a ttl keeps the value", forever.peek("k") is not None)


def _demo_checks(checks: Checks) -> None:
    steps = demo.run()
    checks.equal("four scenarios", len(steps), 4)
    for step in steps:
        checks.ok(f"scenario as advertised: {step.scenario}", step.ok)
    checks.ok("the footer counts misses", "0 not as advertised" in demo.render(steps))


GROUPS = (
    ("model", _model_checks),
    ("threads", _thread_checks),
    ("failure", _failure_checks),
    ("ttl", _ttl_checks),
    ("demo", _demo_checks),
)


def run() -> tuple[int, int]:
    checks = Checks()
    for _name, group in GROUPS:
        group(checks)
    return checks.passed, checks.total
