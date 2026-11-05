from pathlib import Path

import pytest

from {{ package_name }} import consumer as consumer_mod
from {{ package_name }}.store import Store


def test_a_duplicate_is_applied_once(tmp_path: Path) -> None:
    path = tmp_path / "one.db"
    with Store(path) as store:
        _, event = store.place_order(400)
        with consumer_mod.Consumer(path, "ledger") as consumer:
            assert consumer.apply(event) is True
            assert consumer.apply(event) is False
            assert consumer.total(event.aggregate) == 400
            assert consumer.applied_count() == 1


def test_two_consumers_keep_separate_ledgers(tmp_path: Path) -> None:
    path = tmp_path / "two.db"
    with Store(path) as store:
        _, event = store.place_order(250)
        with (
            consumer_mod.Consumer(path, "ledger") as first,
            consumer_mod.Consumer(path, "audit") as second,
        ):
            assert first.apply(event) is True
            assert second.apply(event) is True
            assert first.total(event.aggregate) == second.total(event.aggregate) == 250


def test_order_is_checked_not_assumed(tmp_path: Path) -> None:
    path = tmp_path / "order.db"
    with Store(path) as store:
        order, placed = store.place_order(100)
        paid = store.pay_order(order.ident)
        with consumer_mod.Consumer(path, "ledger") as consumer:
            assert consumer.apply(placed) is True
            assert consumer.apply(paid) is True
            assert consumer.last_seq(placed.aggregate) == 2
        second, _ = store.place_order(50)
        paid_second = store.pay_order(second.ident)
        with consumer_mod.Consumer(path, "late") as consumer:
            with pytest.raises(consumer_mod.ConsumerError, match="got seq 2 after 0"):
                consumer.apply(paid_second)
            assert consumer.applied_count() == 0


def test_handle_counts_repeats(tmp_path: Path) -> None:
    path = tmp_path / "handle.db"
    with Store(path) as store:
        _, event = store.place_order(700)
        with consumer_mod.Consumer(path, "ledger") as consumer:
            handled = consumer.handle([event, event])
            assert handled.applied_count == 1
            assert handled.duplicate_count == 1
            assert handled.line() == "applied 1, duplicates 1"


def test_a_consumer_needs_a_name(tmp_path: Path) -> None:
    with pytest.raises(consumer_mod.ConsumerError, match="needs a name"):
        consumer_mod.Consumer(tmp_path / "x.db", "")
