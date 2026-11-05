"""The relay: read the outbox, publish, then mark — in that order, always.

Two guarantees, both cheap and both tested:

* nothing is marked before it is published, so a crash re-publishes (duplicates
  are the price of at-least-once, and the consumer's ledger pays it);
* an aggregate's events are published in order, because an event whose
  predecessor failed is skipped rather than overtaken.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from .model import Event
from .store import Store

Sink = Callable[[Event], None]


class SinkError(RuntimeError):
    """The broker refused this event. It stays pending and its successors wait."""


@dataclass
class Report:
    delivered: list[str] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)
    crashed_at: str | None = None

    @property
    def delivered_count(self) -> int:
        return len(self.delivered)

    @property
    def blocked_count(self) -> int:
        return len(self.blocked)

    def line(self) -> str:
        head = f"delivered {self.delivered_count}, blocked {self.blocked_count}"
        if self.crashed_at is None:
            return head
        return f"{head}, crashed before marking {self.crashed_at[:12]}"


def publish(
    store: Store, sink: Sink, *, limit: int = 50, crash_after: int | None = None
) -> Report:
    """Publish pending events in outbox order.

    `crash_after=n` models the process dying right after the sink accepted the
    nth event and before the row was marked — the exact window that makes
    at-least-once delivery a real property rather than a slogan.
    """
    if crash_after is not None and crash_after < 1:
        raise ValueError(f"crash_after must be at least 1, got {crash_after}")
    report = Report()
    stuck: set[str] = set()
    for event in store.unpublished(limit=limit):
        if event.aggregate in stuck:
            report.blocked.append(event.event_id)
            continue
        try:
            sink(event)
        except SinkError:
            stuck.add(event.aggregate)
            report.blocked.append(event.event_id)
            continue
        if crash_after is not None and len(report.delivered) + 1 >= crash_after:
            report.crashed_at = event.event_id
            break
        store.mark_published(event.event_id)
        report.delivered.append(event.event_id)
    return report


def replay(sink: Sink, events: list[Event]) -> list[str]:
    """Publish events already in hand — what a broker redelivery looks like."""
    ids = []
    for event in events:
        sink(event)
        ids.append(event.event_id)
    return ids
