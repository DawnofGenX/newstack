from __future__ import annotations

import pytest

from {{ package_name }} import world as subject

World = subject.World


def test_a_message_is_stamped_later_on_the_receiver() -> None:
    world = World({"a": 500, "b": 0}, start_ms=1_000)
    world.tick(0)
    sent, received = world.send("a", "b")
    assert sent < received
    assert received.node == "b"
    assert world.violations() == []


def test_the_world_counts_what_each_node_saw() -> None:
    world = World({"a": 0, "b": 0}, start_ms=1_000)
    world.tick(0)
    world.local("a")
    world.send("a", "b")
    assert world.clock("a").events == 2
    assert world.clock("b").receives == 1
    assert len(world.messages) == 1


def test_time_passes_for_every_node_at_once() -> None:
    world = World({"a": 0, "b": 200}, start_ms=1_000)
    world.tick(50)
    assert world.wall("a").now() == 1_050
    assert world.wall("b").now() == 1_250


def test_a_step_back_moves_only_one_wall() -> None:
    world = World({"a": 0, "b": 0}, start_ms=1_000)
    world.step_back("a", 400)
    assert world.wall("a").now() == 600
    assert world.wall("b").now() == 1_000


def test_a_step_back_does_not_move_the_stamp_back() -> None:
    world = World({"a": 0}, start_ms=1_000)
    first = world.local("a")
    world.step_back("a", 400)
    second = world.local("a")
    assert second > first


def test_an_unknown_node_is_named_in_the_refusal() -> None:
    world = World({"a": 0}, start_ms=1_000)
    with pytest.raises(subject.WorldError, match="unknown node 'z'"):
        world.clock("z")


def test_a_world_needs_a_node() -> None:
    with pytest.raises(subject.WorldError, match="at least one node"):
        World({})


def test_time_cannot_run_backwards_through_tick() -> None:
    world = World({"a": 0}, start_ms=1_000)
    with pytest.raises(subject.WorldError, match="backwards"):
        world.tick(-1)


def test_a_step_back_must_be_positive() -> None:
    world = World({"a": 0}, start_ms=1_000)
    with pytest.raises(subject.WorldError, match="positive"):
        world.step_back("a", 0)


def test_the_report_names_every_node() -> None:
    world = World({"a": 0, "b": 250}, start_ms=1_000)
    world.tick(0)
    world.send("b", "a")
    lines = world.reports()
    assert lines[0].split() == ["node", "physical_ms", "logical", "wall_ms", "skew_ms"]
    assert any(line.startswith("a") for line in lines[1:])
    assert len(lines) == 3


def test_the_max_skew_is_the_worst_node() -> None:
    world = World({"a": 0, "b": 0}, start_ms=1_000)
    world.tick(0)
    world.local("b")
    world.step_back("a", 300)
    world.local("b")
    assert world.max_skew() >= 0


def test_as_dict_carries_the_evidence() -> None:
    world = World({"a": 0}, start_ms=1_000)
    world.tick(0)
    world.local("a", "one")
    payload = world.as_dict()
    assert payload["nodes"]["a"]["events"] == 1
    assert payload["messages"] == 0
    assert payload["violations"] == []
