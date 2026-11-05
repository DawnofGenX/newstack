from {{ package_name }} import relay as relay_mod
from {{ package_name }}.store import Store


def test_publishing_marks_what_it_delivered(store: Store) -> None:
    _, first = store.place_order(100)
    _, second = store.place_order(200)
    seen = []
    report = relay_mod.publish(store, seen.append)
    assert [e.event_id for e in seen] == [first.event_id, second.event_id]
    assert report.delivered == [first.event_id, second.event_id]
    assert report.blocked == []
    assert store.pending_count() == 0


def test_a_crash_after_the_sink_leaves_the_event_pending(store: Store) -> None:
    _, event = store.place_order(100)
    seen = []
    report = relay_mod.publish(store, seen.append, crash_after=1)
    assert len(seen) == 1
    assert report.crashed_at == event.event_id
    assert report.delivered == []
    assert store.pending_count() == 1


def test_the_second_run_delivers_the_duplicate(store: Store) -> None:
    _, event = store.place_order(100)
    seen = []
    relay_mod.publish(store, seen.append, crash_after=1)
    relay_mod.publish(store, seen.append)
    assert [e.event_id for e in seen] == [event.event_id, event.event_id]


def test_a_refused_event_holds_back_its_aggregate(store: Store) -> None:
    order, placed = store.place_order(900)
    paid = store.pay_order(order.ident)
    _, other = store.place_order(500)
    stuck = {"on": True}
    seen = []

    def sink(event) -> None:
        if stuck["on"] and event.aggregate == placed.aggregate:
            raise relay_mod.SinkError("broker down")
        seen.append(event)

    report = relay_mod.publish(store, sink)
    assert report.blocked == [placed.event_id, paid.event_id]
    assert report.delivered == [other.event_id]
    assert store.get(paid.event_id).published is False
    stuck["on"] = False
    after = relay_mod.publish(store, sink)
    assert after.delivered == [placed.event_id, paid.event_id]


def test_limit_bounds_one_pass(store: Store) -> None:
    for amount in (100, 200, 300):
        store.place_order(amount)
    report = relay_mod.publish(store, lambda event: None, limit=2)
    assert report.delivered_count == 2
    assert store.pending_count() == 1


def test_crash_after_zero_is_refused(store: Store) -> None:
    import pytest

    with pytest.raises(ValueError, match="crash_after must be at least 1"):
        relay_mod.publish(store, lambda event: None, crash_after=0)


def test_the_sink_can_see_the_envelope(store: Store) -> None:
    store.place_order(100)
    envelopes = []
    relay_mod.publish(store, lambda event: envelopes.append(event.envelope()))
    assert envelopes[0]["version"] == 1
    assert envelopes[0]["payload"] == {"amount": 100, "order": 1}
