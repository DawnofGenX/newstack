import json

import pytest

from {{ package_name }} import network as subject
from {{ package_name }} import orset


def _canon(state: object) -> str:
    dumped = state.as_dict()  # type: ignore[attr-defined]
    return json.dumps(dumped, sort_keys=True, separators=(",", ":"))


def test_gossip_converges() -> None:
    replicas = [
        orset.ORSet().add("x", "a"),
        orset.ORSet().add("y", "b"),
        orset.ORSet().add("z", "c"),
    ]
    flowed = subject.gossip(replicas, orset.ORSet.merge, _canon, seed=5)
    assert flowed.converged
    assert all(item.elements() == {"x", "y", "z"} for item in flowed.replicas)


def test_duplicated_delivery_is_harmless() -> None:
    replicas = [orset.ORSet().add("x", "a"), orset.ORSet().add("y", "b")]
    flowed = subject.gossip(replicas, orset.ORSet.merge, _canon, seed=1, duplicates=3)
    assert len(set(flowed.states)) == 1


def test_the_same_seed_gives_the_same_order() -> None:
    replicas = [
        orset.ORSet().add("x", "a"),
        orset.ORSet().add("y", "b"),
        orset.ORSet().add("z", "c"),
    ]
    first = subject.gossip(replicas, orset.ORSet.merge, _canon, seed=4)
    second = subject.gossip(replicas, orset.ORSet.merge, _canon, seed=4)
    assert first.states == second.states


def test_a_single_replica_is_refused() -> None:
    with pytest.raises(ValueError):
        subject.gossip([orset.ORSet()], orset.ORSet.merge, _canon)


def test_deliveries_are_counted() -> None:
    replicas = [orset.ORSet().add("x", "a"), orset.ORSet().add("y", "b")]
    flowed = subject.gossip(replicas, orset.ORSet.merge, _canon, seed=2, rounds=2, duplicates=2)
    assert flowed.deliveries == 2 * 2 * 2


def test_the_report_says_when_replicas_disagree() -> None:
    class Stubborn:
        def __init__(self, value: int) -> None:
            self.value = value

    flowed = subject.gossip(
        [Stubborn(1), Stubborn(2)], lambda left, right: left, lambda state: str(state.value)
    )
    assert not flowed.converged
    assert "DISAGREE" in flowed.lines()[0]
