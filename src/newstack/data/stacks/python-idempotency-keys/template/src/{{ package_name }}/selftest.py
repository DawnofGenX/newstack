"""Checks with no framework, so they run from the installed command too."""

from __future__ import annotations

import tempfile
import threading
from pathlib import Path

from . import demo, guard, model
from .store import Store


class Clock:
    """A clock the checks move, so a lease costs no wall time."""

    def __init__(self, start: float = 1_800_000_000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class Checks:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0
        self.total = 0

    def ok(self, description: str, condition: bool) -> None:
        self.total += 1
        if condition:
            self.passed += 1
            print(f"ok    {description}")
        else:
            self.failed += 1
            print(f"FAIL  {description}")

    def equal(self, description: str, want, got) -> None:
        self.total += 1
        if want == got:
            self.passed += 1
            print(f"ok    {description}")
        else:
            self.failed += 1
            print(f"FAIL  {description}: want {want!r}, got {got!r}")

    def raises(self, description: str, function, *args, **kwargs) -> None:
        self.total += 1
        try:
            function(*args, **kwargs)
        except Exception:
            self.passed += 1
            print(f"ok    {description}")
            return
        self.failed += 1
        print(f"FAIL  {description}: nothing was raised")


def _request(key: str = "order-8f3a1c2d", amount: int = 1200) -> model.Request:
    return model.Request(scope="charge", key=key, body={"amount": amount})


def _model_checks(checks: Checks) -> None:
    checks.raises("a key shorter than eight characters is refused", model.Request, "c", "short", {})
    checks.raises(
        "a key with a space is refused", model.Request, "charge", "order 8f3a1c2d", {}
    )
    checks.raises("an empty scope is refused", model.Request, "  ", "order-8f3a1c2d", {})
    checks.raises("a non-mapping body is refused", model.Request, "charge", "order-8f3a1c2d", [1])
    body = {"amount": 1200, "currency": "USD"}
    reordered = {"currency": "USD", "amount": 1200}
    checks.equal(
        "key order does not change the fingerprint",
        model.fingerprint_of("charge", body),
        model.fingerprint_of("charge", reordered),
    )
    checks.ok(
        "a different scope is a different request",
        model.fingerprint_of("charge", body) != model.fingerprint_of("refund", body),
    )
    total = model.fingerprint_of("charge", body)
    checks.equal("the fingerprint is 16 hex characters", 16, len(total))
    checks.raises("a status outside 100-599 is refused", model.Response, 42, "{}")
    checks.raises("a boolean status is refused", model.Response, True, "{}")
    checks.raises("a non-text body is refused", model.Response, 200, {"ok": True})


def _store_checks(checks: Checks, directory: Path) -> None:
    clock = Clock()
    store = Store(directory / "store.db", clock=clock)
    try:
        request = _request()
        claim = store.claim(request)
        checks.ok("a fresh key is not a replay", claim.fresh)
        checks.equal("a fresh claim is attempt 1", 1, claim.attempt)
        checks.raises("a live claim cannot be claimed twice", store.claim, request)
        other_body = _request(amount=9)
        checks.raises("a different body on the same key is a mismatch", store.claim, other_body)
        store.complete(request, claim.attempt, model.Response(201, '{"charged": 1200}'))
        replay = store.claim(request)
        checks.ok("a completed key replays", replay.replay)
        checks.equal("the replay carries the stored status", 201, replay.status)
        checks.equal("the replay carries the stored body", '{"charged": 1200}', replay.body)
        checks.raises(
            "the store refuses to complete an attempt that no longer owns the row",
            store.complete,
            request,
            claim.attempt,
            model.Response(201, "{}"),
        )
        checks.equal("one key is on file", 1, store.count())
        checks.equal("one key is completed", 1, store.count("completed"))
    finally:
        store.close()

    clock2 = Clock()
    path = directory / "lease.db"
    first = Store(path, clock=clock2)
    try:
        request = _request(key="order-lease001")
        claim = first.claim(request)
        checks.raises("a second claim while the lease is live is refused", first.claim, request)
        clock2.advance(31.0)
        takeover = first.claim(request)
        checks.equal("after the lease the key is taken over", 2, takeover.attempt)
        checks.raises(
            "the old attempt cannot write its result",
            first.complete,
            request,
            claim.attempt,
            model.Response(201, "{}"),
        )
        first.complete(request, takeover.attempt, model.Response(201, '{"charged": 1200}'))
        checks.ok("the takeover can complete", first.claim(request).replay)
    finally:
        first.close()

    clock3 = Clock()
    path = directory / "release.db"
    releasing = Store(path, clock=clock3)
    try:
        request = _request(key="order-rel00001")
        claim = releasing.claim(request)
        releasing.release(request, claim.attempt)
        again = releasing.claim(request)
        checks.equal("a released key is claimable at once", 2, again.attempt)
        releasing.complete(request, again.attempt, model.Response(201, "{}"))
        clock3.advance(3600.0)
        checks.equal("an old completed key is pruned", 1, releasing.prune(60.0))
        checks.equal("pruning leaves the table empty", 0, releasing.count())
    finally:
        releasing.close()

    states = Store(directory / "states.db", clock=Clock())
    try:
        checks.raises("an unknown state is refused", states.count, "half-done")
    finally:
        states.close()


def _guard_checks(checks: Checks, directory: Path) -> None:
    clock = Clock()
    with Store(directory / "guard.db", clock=clock) as store:
        calls: list[int] = []

        def handler(request: model.Request) -> model.Response:
            calls.append(int(request.body["amount"]))
            return model.Response(201, '{"charged": 1200}')

        first = guard.execute(store, _request(key="order-guard001"), handler)
        second = guard.execute(store, _request(key="order-guard001"), handler)
        checks.ok("the first call executes", first.executed)
        checks.ok("the second call replays", second.replay)
        checks.equal("the handler ran once", 1, len(calls))

        def broken(request: model.Request) -> model.Response:
            raise RuntimeError("provider said no")

        checks.raises(
            "a handler that raises lets the error through",
            guard.execute,
            store,
            _request(key="order-guard002"),
            broken,
        )
        retried = guard.execute(store, _request(key="order-guard002"), handler)
        checks.equal("a failed key is retryable without waiting", 2, retried.attempts)

        slow_clock = Clock()
        expiring = Store(directory / "expire.db", clock=slow_clock)
        rival = Store(directory / "expire.db", clock=slow_clock)
        try:
            stale = expiring.claim(_request(key="order-guard003"), lease_s=30.0)
            slow_clock.advance(31.0)
            takeover = rival.claim(_request(key="order-guard003"))
            checks.equal("an expired claim is taken over", 2, takeover.attempt)
            checks.raises(
                "the worker that lost the lease cannot store its result",
                expiring.complete,
                _request(key="order-guard003"),
                stale.attempt,
                model.Response(201, "{}"),
            )
        finally:
            rival.close()
            expiring.close()


def _concurrency_checks(checks: Checks, directory: Path) -> None:
    clock = Clock()
    path = directory / "race.db"
    calls: list[int] = []
    lock = threading.Lock()
    started = threading.Barrier(4)
    results: list[str] = []

    def handler(request: model.Request) -> model.Response:
        with lock:
            calls.append(1)
        return model.Response(201, '{"charged": 1200}')

    def worker() -> None:
        store = Store(path, clock=clock)
        try:
            started.wait(timeout=5)
            outcome = guard.execute(store, _request(key="order-race0001"), handler)
            results.append("replay" if outcome.replay else "execute")
        except model.InProgress:
            results.append("refused")
        finally:
            store.close()

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    checks.equal("four workers produced four answers", 4, len(results))
    checks.equal("only one of them called the handler", 1, len(calls))
    checks.equal("exactly one answer is an execute", 1, results.count("execute"))


def _demo_checks(checks: Checks, directory: Path) -> None:
    steps = demo.run(directory / "demo")
    checks.equal("the demo runs four scenarios", 4, len(steps))
    checks.ok("every scenario is as advertised", all(step.ok for step in steps))
    checks.ok("the render says so", "0 not as advertised" in demo.render(steps))
    payload = demo.payload(steps)
    checks.equal("the payload counts no misses", 0, payload["missed"])
    checks.equal("the payload lists every scenario", 4, len(payload["scenarios"]))


def run() -> tuple[int, int, int]:
    checks = Checks()
    with tempfile.TemporaryDirectory(prefix="idem-selftest-") as raw:
        directory = Path(raw)
        _model_checks(checks)
        _store_checks(checks, directory)
        _guard_checks(checks, directory)
        _concurrency_checks(checks, directory)
        _demo_checks(checks, directory)
    return checks.passed, checks.failed, checks.total
