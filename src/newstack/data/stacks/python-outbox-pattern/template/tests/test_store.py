from pathlib import Path

import pytest

from {{ package_name }} import store as store_mod

Store = store_mod.Store


def test_placing_an_order_writes_the_row_and_the_event(store) -> None:
    order, event = store.place_order(1200)
    assert order.status == "placed"
    assert event.seq == 1
    assert event.aggregate == f"order:{order.ident}"
    assert event.payload == {"amount": 1200, "order": order.ident}
    assert not event.published
    assert store.pending_count() == 1
    assert store.count() == 1


def test_paying_appends_a_second_event_and_changes_the_row(store) -> None:
    order, placed = store.place_order(900)
    paid = store.pay_order(order.ident)
    assert (placed.seq, paid.seq) == (1, 2)
    assert store.order(order.ident).status == "paid"
    assert store.count() == 2


def test_paying_twice_is_refused(store) -> None:
    order, _ = store.place_order(900)
    store.pay_order(order.ident)
    with pytest.raises(store_mod.InputError, match="already paid"):
        store.pay_order(order.ident)


def test_sequences_are_per_aggregate(store) -> None:
    _, first = store.place_order(100)
    _, second = store.place_order(200)
    assert first.seq == second.seq == 1
    assert first.aggregate != second.aggregate
    assert second.position > first.position


def test_the_unsafe_path_leaves_an_order_with_no_event(store) -> None:
    order = store.place_order_unsafe(700)
    assert store.order(order.ident).amount == 700
    assert store.count() == 0
    assert store.pending_count() == 0


@pytest.mark.parametrize("amount", [0, -5, True, 1.5, "10"])
def test_amounts_must_be_positive_integers(store, amount) -> None:
    with pytest.raises(store_mod.InputError, match="amount must be"):
        store.place_order(amount)


def test_marking_is_idempotent(store) -> None:
    _, event = store.place_order(100)
    assert store.mark_published(event.event_id) is True
    assert store.mark_published(event.event_id) is False
    assert store.pending_count() == 0
    assert store.get(event.event_id).published


def test_unpublished_is_in_write_order(store) -> None:
    _, first = store.place_order(100)
    _, second = store.place_order(200)
    assert [e.event_id for e in store.unpublished()] == [first.event_id, second.event_id]
    store.mark_published(first.event_id)
    assert [e.event_id for e in store.unpublished()] == [second.event_id]


def test_the_outbox_survives_a_reopen(tmp_path: Path) -> None:
    path = tmp_path / "reopen.db"
    with Store(path) as first:
        _, event = first.place_order(100)
        first.mark_published(event.event_id)
    with Store(path) as second:
        assert second.count() == 1
        assert second.pending_count() == 0
        assert second.get(event.event_id).published


def test_unknown_rows_are_named(store) -> None:
    with pytest.raises(store_mod.StoreError, match="no order 99"):
        store.order(99)
    with pytest.raises(store_mod.StoreError, match="no event 'nope'"):
        store.get("nope")


def test_a_zero_limit_is_refused(store) -> None:
    with pytest.raises(store_mod.InputError, match="limit must be at least 1"):
        store.unpublished(limit=0)
