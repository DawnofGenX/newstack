"""Four scenarios, each measuring the number of effects, not the number of answers."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import guard, model
from .store import Store

AMOUNT = 1200


class Ledger:
    """Stands in for the payment provider: it counts how many times it was called."""

    def __init__(self) -> None:
        self.charges: list[int] = []
        self._lock = threading.Lock()

    def charge(self, request: model.Request) -> model.Response:
        amount = int(request.body.get("amount", 0))
        with self._lock:
            self.charges.append(amount)
        return model.Response(status=201, body=json.dumps({"charged": amount}, sort_keys=True))

    @property
    def total(self) -> int:
        return sum(self.charges)


@dataclass(frozen=True)
class Step:
    scenario: str
    lines: list[str]
    ok: bool

    def render(self) -> str:
        verdict = "as advertised" if self.ok else "NOT AS ADVERTISED"
        body = "\n".join(f"  {line}" for line in self.lines)
        return f"{self.scenario:<42} {verdict}\n{body}"


def _request(key: str, amount: int = AMOUNT) -> model.Request:
    return model.Request(scope="charge", key=key, body={"amount": amount, "currency": "USD"})


def _store(path: Path, clock: Callable[[], float]) -> Store:
    return Store(path, clock=clock)


def _sequential(directory: Path) -> Step:
    clock = _Clock()
    ledger = Ledger()
    with _store(directory / "sequential.db", clock) as store:
        first = guard.execute(store, _request("order-8f3a1c2d"), ledger.charge)
        second = guard.execute(store, _request("order-8f3a1c2d"), ledger.charge)
    lines = [
        f"first call   {first.line()}",
        f"second call  {second.line()}",
        f"the provider was called {len(ledger.charges)} time(s) for {ledger.total} minor units",
    ]
    ok = first.executed and second.replay and len(ledger.charges) == 1
    return Step("the same request sent twice", lines, ok)


def _concurrent(directory: Path) -> Step:
    clock = _Clock()
    ledger = Ledger()
    path = directory / "concurrent.db"
    started = threading.Barrier(2)
    results: list[str] = []

    def handler(request: model.Request) -> model.Response:
        time.sleep(0.05)
        return ledger.charge(request)

    def worker(name: str) -> None:
        store = _store(path, clock)
        try:
            started.wait(timeout=5)
            outcome = guard.execute(store, _request("order-2b9d7e10"), handler)
            results.append(f"{name}: {outcome.line()}")
        except model.InProgress as error:
            results.append(f"{name}: refused, retry in {error.retry_after_s:.1f}s")
        finally:
            store.close()

    first = threading.Thread(target=worker, args=("worker a",))
    second = threading.Thread(target=worker, args=("worker b",))
    first.start()
    second.start()
    first.join(timeout=10)
    second.join(timeout=10)
    lines = [
        *sorted(results),
        f"the provider was called {len(ledger.charges)} time(s) for {ledger.total} minor units",
        "one worker holds the lease while it runs; the other is told to retry",
    ]
    ok = len(ledger.charges) == 1
    return Step("two workers, one key", lines, ok)


def _different_body(directory: Path) -> Step:
    clock = _Clock()
    ledger = Ledger()
    lines: list[str] = []
    with _store(directory / "mismatch.db", clock) as store:
        first = guard.execute(store, _request("order-51cc0a77"), ledger.charge)
        lines.append(f"first call   {first.line()}")
        try:
            guard.execute(store, _request("order-51cc0a77", amount=9900), ledger.charge)
        except model.Mismatch as error:
            lines.append(f"second call  refused: {error}")
        lines.append(f"the provider was called {len(ledger.charges)} time(s) for {ledger.total}")
    ok = len(ledger.charges) == 1
    return Step("the same key with a different body", lines, ok)


def _crash(directory: Path) -> Step:
    """The honest failure: the effect happened, the row never learned about it."""
    clock = _Clock()
    ledger = Ledger()
    path = directory / "crash.db"
    request = _request("order-dead00ff")
    store = _store(path, clock)
    try:
        claim = store.claim(request)
        ledger.charge(request)
        lines = [
            f"attempt {claim.attempt} charged and then the process died before the row",
            f"the provider was called {len(ledger.charges)} time(s) so far",
        ]
    finally:
        store.close()
    clock.advance(31.0)
    with _store(path, clock) as second:
        claim = second.claim(request)
        second.complete(request, claim.attempt, ledger.charge(request))
        lines.append(f"after the lease expired the key was taken over as attempt {claim.attempt}")
        lines.append(f"the provider was called {len(ledger.charges)} time(s) for {ledger.total}")
        lines.append("nothing in the key table can undo an effect that already happened")
    ok = len(ledger.charges) == 2
    return Step("a crash between the effect and the row", lines, ok)


class _Clock:
    """A clock the scenario can move, so a 30 second lease costs no seconds."""

    def __init__(self, start: float = 1_800_000_000.0) -> None:
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


SCENARIOS: tuple[tuple[str, Callable[[Path], Step]], ...] = (
    ("sequential", _sequential),
    ("concurrent", _concurrent),
    ("mismatch", _different_body),
    ("crash", _crash),
)


def run(directory: Path) -> list[Step]:
    directory.mkdir(parents=True, exist_ok=True)
    return [builder(directory) for _, builder in SCENARIOS]


def render(steps: list[Step]) -> str:
    missed = sum(1 for step in steps if not step.ok)
    body = "\n\n".join(step.render() for step in steps)
    footer = f"demo: {len(steps)} scenarios, {missed} not as advertised"
    return f"{body}\n\n{footer}"


def payload(steps: list[Step]) -> dict[str, Any]:
    return {
        "scenarios": [
            {"scenario": step.scenario, "ok": step.ok, "lines": step.lines} for step in steps
        ],
        "missed": sum(1 for step in steps if not step.ok),
    }
