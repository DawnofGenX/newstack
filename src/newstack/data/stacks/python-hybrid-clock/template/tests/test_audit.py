from __future__ import annotations

from {{ package_name }} import audit as subject
from {{ package_name }}.stamp import Stamp
from {{ package_name }}.world import Entry, World


def test_a_sequence_of_stamps_is_strictly_increasing() -> None:
    stamps = [Stamp(1, 0, "a"), Stamp(1, 1, "a"), Stamp(2, 0, "a")]
    assert subject.is_strictly_increasing(stamps)
    assert not subject.is_strictly_increasing([Stamp(2, 0, "a"), Stamp(1, 0, "a")])


def test_stamp_order_ignores_the_wall() -> None:
    entries = [
        Entry("local", "b", Stamp(1_000, 0, "b"), 1_000),
        Entry("send", "a", Stamp(1_500, 0, "a"), 1_500),
        Entry("receive", "b", Stamp(1_500, 1, "b"), 1_000),
    ]
    ordered = [entry.kind for entry in subject.order_by_stamp(entries)]
    assert ordered == ["local", "send", "receive"]


def test_the_wall_order_puts_the_receipt_first() -> None:
    entries = [
        Entry("local", "b", Stamp(1_000, 0, "b"), 1_000),
        Entry("send", "a", Stamp(1_500, 0, "a"), 1_500),
        Entry("receive", "b", Stamp(1_500, 1, "b"), 1_000),
    ]
    ordered = [entry.kind for entry in subject.order_by_wall(entries)]
    assert ordered.index("receive") < ordered.index("send")


def test_inversions_are_counted_and_explained() -> None:
    entries = [
        Entry("local", "b", Stamp(1_000, 0, "b"), 1_000),
        Entry("send", "a", Stamp(1_500, 0, "a"), 1_500),
        Entry("receive", "b", Stamp(1_500, 1, "b"), 1_000),
    ]
    found = subject.disagreements(entries)
    assert found
    assert "the wall says" in found[0].line()


def test_a_consistent_world_has_no_inversions() -> None:
    world = World({"a": 0, "b": 0}, start_ms=1_000)
    world.tick(0)
    world.local("a")
    world.tick(10)
    world.local("b")
    assert subject.disagreements(world.entries) == []


def test_causality_breaks_are_found_in_pairs() -> None:
    sent = Stamp(2_000, 0, "a")
    received = Stamp(1_000, 0, "b")
    assert subject.causality_breaks([(sent, received)])
    assert subject.causality_breaks([(sent, Stamp(2_000, 1, "b"))]) == []


def test_monotone_reads_each_node_separately() -> None:
    entries = [
        Entry("local", "a", Stamp(1_000, 0, "a"), 1_000),
        Entry("local", "b", Stamp(1_500, 0, "b"), 1_500),
        Entry("local", "a", Stamp(1_600, 0, "a"), 1_600),
    ]
    assert subject.monotone(entries)


def test_monotone_catches_a_node_going_backwards() -> None:
    entries = [
        Entry("local", "a", Stamp(1_600, 0, "a"), 1_600),
        Entry("local", "a", Stamp(1_000, 0, "a"), 1_000),
    ]
    assert not subject.monotone(entries)


def test_coverage_counts_events_and_receipts() -> None:
    world = World({"a": 0, "b": 0}, start_ms=1_000)
    world.tick(0)
    world.local("a")
    world.send("a", "b")
    seen = subject.coverage(world)
    assert seen["a"]["events"] == 2
    assert seen["b"]["receives"] == 1
    assert seen["b"]["skew_ms"] >= 0
