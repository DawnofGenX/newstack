"""The checks that do not need pytest: the guarantees, one assertion each."""

from __future__ import annotations

import tempfile
from pathlib import Path

from . import demo as demo_mod
from .consumer import Consumer, ConsumerError
from .model import Event, InputError, payload_text
from .relay import SinkError, publish
from .store import Store, StoreError


class Checks:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0
        self.failures: list[str] = []

    def ok(self, description: str, condition: bool) -> None:
        if condition:
            self.passed += 1
            return
        self.failed += 1
        self.failures.append(description)

    def equal(self, description: str, want: object, got: object) -> None:
        self.ok(f"{description} (wanted {want!r}, got {got!r})", want == got)

    def raises(self, description: str, function, *args, **kwargs) -> None:
        try:
            function(*args, **kwargs)
        except (InputError, StoreError, ConsumerError, SinkError, ValueError):
            self.passed += 1
            return
        self.failed += 1
        self.failures.append(f"{description} (nothing raised)")


def _model_checks(checks: Checks) -> None:
    text = payload_text({"b": 2, "a": 1})
    checks.equal("payload_text sorts its keys", '{"a":1,"b":2}', text)
    checks.ok("payload_text is compact", ", " not in text and ": " not in text)
    checks.raises("payload_text refuses a list", payload_text, [1, 2])
    checks.raises("payload_text refuses a set", payload_text, {"a": {1, 2}})
    event = Event(event_id="a" * 32, aggregate="order:1", seq=1, kind="order.placed",
                  payload={"amount": 5}, created_at="2026-01-01T00:00:00+00:00")
    checks.equal("a fresh event is not published", False, event.published)
    checks.equal("the envelope carries the version", 1, event.envelope()["version"])
    checks.ok("the envelope hides the outbox position", "position" not in event.envelope())


def _store_checks(checks: Checks, directory: Path) -> None:
    path = directory / "store.db"
    store = Store(path)
    try:
        order, event = store.place_order(1200)
        checks.equal("the first event is seq 1", 1, event.seq)
        checks.equal("the order is placed", "placed", order.status)
        checks.equal("one event is pending", 1, store.pending_count())
        checks.equal("the event aggregates its order", f"order:{order.ident}", event.aggregate)
        checks.equal("the payload holds the amount", 1200, event.payload["amount"])

        paid = store.pay_order(order.ident)
        checks.equal("paying appends seq 2", 2, paid.seq)
        checks.equal("the order is paid", "paid", store.order(order.ident).status)
        checks.raises("paying twice is refused", store.pay_order, order.ident)

        _, other_event = store.place_order(500)
        checks.equal("a second aggregate starts at seq 1", 1, other_event.seq)
        checks.ok("positions increase with every write", other_event.position > paid.position)
        checks.equal("three events exist", 3, store.count())

        pending = store.unpublished()
        checks.equal("unpublished returns them in write order", [event.seq, paid.seq,
                      other_event.seq], [pending[0].seq, pending[1].seq, pending[2].seq])
        checks.equal("mark_published reports the first mark", True,
                     store.mark_published(event.event_id))
        checks.equal("marking twice reports nothing changed", False,
                     store.mark_published(event.event_id))
        checks.equal("two events are still pending", 2, store.pending_count())
        checks.equal("pending_only filters", 2, len(store.events(pending_only=True)))
        checks.equal("the aggregate filter works", 2, len(store.events(aggregate=event.aggregate)))
        checks.equal("limit is honoured", 1, len(store.events(limit=1)))

        unsafe = store.place_order_unsafe(700)
        checks.equal("the unsafe path writes no event", 3, store.count())
        checks.equal("but it does write the order", "placed", store.order(unsafe.ident).status)

        checks.raises("a zero amount is refused", store.place_order, 0)
        checks.raises("a negative amount is refused", store.place_order, -5)
        checks.raises("a boolean amount is refused", store.place_order, True)
        checks.raises("a float amount is refused", store.place_order, 1.5)
        checks.raises("an unknown order is refused", store.order, 999)
        checks.raises("a zero limit is refused", store.unpublished, limit=0)
        checks.raises("an unknown event is refused", store.get, "nope")
    finally:
        store.close()

    reopened = Store(path)
    try:
        checks.equal("the outbox survives a reopen", 3, reopened.count())
        checks.equal("so does the marks", 2, reopened.pending_count())
    finally:
        reopened.close()


def _relay_checks(checks: Checks, directory: Path) -> None:
    store = Store(directory / "relay.db")
    try:
        _, first = store.place_order(100)
        _, second = store.place_order(200)
        seen: list[Event] = []
        report = publish(store, seen.append)
        checks.equal("the relay delivers everything pending", 2, report.delivered_count)
        checks.equal("and the sink saw both", 2, len(seen))
        checks.equal("nothing is pending afterwards", 0, store.pending_count())
        checks.equal("delivered in write order", [first.event_id, second.event_id],
                     report.delivered)

        _, third = store.place_order(300)
        crashed: list[Event] = []
        crash = publish(store, crashed.append, crash_after=1)
        checks.equal("the sink accepted the event", 1, len(crashed))
        checks.equal("the crash is reported", third.event_id, crash.crashed_at)
        checks.equal("nothing was marked", 1, store.pending_count())
        checks.equal("and nothing was counted as delivered", 0, crash.delivered_count)

        failing = {"on": True}

        def refuse(event: Event) -> None:
            if failing["on"]:
                raise SinkError("nope")
            seen.append(event)

        blocked = publish(store, refuse)
        checks.equal("a refused event is blocked, not delivered", 0, blocked.delivered_count)
        checks.equal("and it is named", [third.event_id], blocked.blocked)
        failing["on"] = False
        retried = publish(store, refuse)
        checks.equal("after the broker recovers it goes through", 1, retried.delivered_count)
        checks.raises("crash_after must be positive", publish, store, seen.append, crash_after=0)
    finally:
        store.close()

    ordering = Store(directory / "ordering.db")
    try:
        order, placed = ordering.place_order(900)
        paid = ordering.pay_order(order.ident)
        stuck = {"on": True}

        def sink(event: Event) -> None:
            if stuck["on"] and event.aggregate == placed.aggregate:
                raise SinkError("broker down")

        report = publish(ordering, sink)
        checks.equal("the refused event and its successor are blocked",
                     [placed.event_id, paid.event_id], report.blocked)
        checks.equal("nothing for that aggregate got through", 0, report.delivered_count)
        stuck["on"] = False
        after = publish(ordering, sink)
        checks.equal("then both go through in order", [placed.event_id, paid.event_id],
                     after.delivered)
    finally:
        ordering.close()


def _consumer_checks(checks: Checks, directory: Path) -> None:
    path = directory / "consumer.db"
    store = Store(path)
    consumer = Consumer(path, "ledger")
    try:
        order, placed = store.place_order(400)
        paid = store.pay_order(order.ident)
        checks.equal("the first delivery applies", True, consumer.apply(placed))
        checks.equal("the same event again does not", False, consumer.apply(placed))
        checks.equal("the total counts it once", 400, consumer.total(placed.aggregate))
        checks.equal("applied_count counts deliveries, not attempts", 1, consumer.applied_count())
        checks.equal("the next seq applies", True, consumer.apply(paid))
        checks.equal("the total is still the placed amount", 400, consumer.total(placed.aggregate))
        checks.equal("last_seq moves to the newest", 2, consumer.last_seq(placed.aggregate))

        second, _ = store.place_order(150)
        skipped = store.pay_order(second.ident)
        checks.raises("a gap in the sequence is refused", consumer.apply, skipped)

        other_consumer = Consumer(path, "audit")
        checks.equal("another consumer has its own ledger", True, other_consumer.apply(placed))
        checks.equal("and its own total", 400, other_consumer.total(placed.aggregate))
        other_consumer.close()
        checks.raises("a consumer needs a name", Consumer, path, "")
    finally:
        consumer.close()
        store.close()


def _demo_checks(checks: Checks, directory: Path) -> None:
    steps = demo_mod.run(directory / "demo")
    checks.equal("the demo has three scenarios", 3, len(steps))
    checks.equal("the dual write loses the event", "lost", steps[0].verdict)
    checks.ok("and that is the point it makes", steps[0].ok)
    checks.equal("the crash scenario ends exactly once", "exactly once", steps[1].verdict)
    checks.ok("with one apply and one duplicate", steps[1].ok)
    checks.equal("the ordering scenario ends in order", "in order", steps[2].verdict)
    checks.ok("and the consumer never saw a gap", steps[2].ok)
    checks.ok("every scenario holds", all(step.ok for step in steps))
    rendered = demo_mod.lines(steps)
    checks.ok("the last line counts the misses", rendered[-1].startswith("demo: 3 scenarios"))


def run(verbose: bool = False) -> int:
    checks = Checks()
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        groups = (
            ("model", lambda: _model_checks(checks)),
            ("store", lambda: _store_checks(checks, root)),
            ("relay", lambda: _relay_checks(checks, root)),
            ("consumer", lambda: _consumer_checks(checks, root)),
            ("demo", lambda: _demo_checks(checks, root)),
        )
        for label, group in groups:
            before = checks.failed
            group()
            if verbose:
                print(f"{label:<10} {checks.passed} passed, {checks.failed - before} failed")
    if checks.failures:
        for failure in checks.failures:
            print(f"FAIL  {failure}")
    print(f"selftest: {checks.passed} checks passed, {checks.failed} failed "
          f"out of {checks.passed + checks.failed}")
    return 0 if checks.failed == 0 else 2
