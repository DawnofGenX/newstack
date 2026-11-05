"""Three scenarios, each with the observation that decides it.

1. the same write, without an outbox: the event is gone and nothing complains;
2. the same write, with an outbox, crashing between publish and mark: the
   consumer sees the event twice and applies it once;
3. an aggregate whose first event the broker refused: its second event waits,
   so the stream the consumer sees is still in order.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .consumer import Consumer
from .relay import SinkError, publish
from .store import Store


@dataclass(frozen=True)
class Step:
    scenario: str
    verdict: str
    lines: tuple[str, ...]
    ok: bool

    def render(self) -> str:
        head = f"{self.scenario:<34} {self.verdict:<13}"
        body = "".join(f"\n    {line}" for line in self.lines)
        return head + body


def _dual_write(directory: Path) -> Step:
    store = Store(directory / "dual.db")
    try:
        order = store.place_order_unsafe(1200)
        # The process dies here. In a real service this is a deploy, a killed
        # pod, or an exception in the code between the two writes.
        events = store.count()
        orders = store.orders()
        lines = (
            f"order {order.ident} is committed, amount {order.amount}",
            f"outbox rows carrying the event: {events}",
            "the order exists and nothing in the database says it happened",
        )
        return Step("the write without an outbox", "lost", lines, events == 0 and orders != [])
    finally:
        store.close()


def _crash_between_publish_and_mark(directory: Path) -> Step:
    path = directory / "crash.db"
    store = Store(path)
    consumer = Consumer(path, "ledger")
    try:
        order, event = store.place_order(1200)
        seen = []
        first = publish(store, seen.append, crash_after=1)
        pending_after_crash = store.pending_count()
        second = publish(store, seen.append)
        handled = consumer.handle(seen)
        total = consumer.total(event.aggregate)
        lines = (
            f"the sink accepted {len(seen)} copy/copies of 1 event",
            f"pending after the crash: {pending_after_crash} (delivered {first.delivered_count})",
            f"the consumer applied {handled.applied_count}, "
            f"dropped {handled.duplicate_count} repeat(s)",
            f"the ledger total is {total} for an order of {order.amount}",
        )
        ok = (
            len(seen) == 2
            and handled.applied_count == 1
            and handled.duplicate_count == 1
            and total == order.amount
            and pending_after_crash == 1
            and second.delivered_count == 1
        )
        return Step("a crash between publish and mark", "exactly once", lines, ok)
    finally:
        consumer.close()
        store.close()


def _ordering(directory: Path) -> Step:
    path = directory / "order.db"
    store = Store(path)
    consumer = Consumer(path, "ledger")
    try:
        first, placed = store.place_order(900)
        paid = store.pay_order(first.ident)
        _, other = store.place_order(500)

        failing = {"on": True}
        delivered = []

        def sink(event) -> None:
            if failing["on"] and event.aggregate == placed.aggregate:
                raise SinkError("broker unavailable")
            delivered.append(event)

        blocked_report = publish(store, sink)
        failing["on"] = False
        rest = publish(store, sink)
        handled = consumer.handle(delivered)
        lines = (
            f"first pass delivered {blocked_report.delivered_count}, "
            f"blocked {blocked_report.blocked_count}",
            f"blocked: seq {paid.seq} of {paid.aggregate}, behind seq {placed.seq}",
            f"second pass delivered {rest.delivered_count} in seq order",
            f"the consumer applied {handled.applied_count}, last seq "
            f"{consumer.last_seq(placed.aggregate)} for {placed.aggregate}",
            f"the other aggregate was never held up: {other.aggregate}",
        )
        ok = (
            blocked_report.blocked == [placed.event_id, paid.event_id]
            and blocked_report.delivered == [other.event_id]
            and handled.applied_count == 3
            and consumer.last_seq(placed.aggregate) == paid.seq
        )
        return Step("a broker that refuses one aggregate", "in order", lines, ok)
    finally:
        consumer.close()
        store.close()


def run(directory: Path) -> list[Step]:
    directory.mkdir(parents=True, exist_ok=True)
    return [
        _dual_write(directory),
        _crash_between_publish_and_mark(directory),
        _ordering(directory),
    ]


def lines(steps: list[Step]) -> list[str]:
    body = [step.render() for step in steps]
    missed = [step for step in steps if not step.ok]
    body.append(f"demo: {len(steps)} scenarios, {len(missed)} not as advertised")
    return body
