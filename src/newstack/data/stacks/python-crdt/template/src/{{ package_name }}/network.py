"""Delivery you cannot control: shuffled, duplicated, and repeated until quiet."""

from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

Merge = Callable[[Any, Any], Any]
Serialise = Callable[[Any], str]


@dataclass(frozen=True)
class Gossip:
    """What the network did, and whether the replicas ended up agreeing."""

    replicas: list[Any]
    deliveries: int
    converged: bool
    states: list[str]

    def lines(self) -> list[str]:
        sender = "agreed" if self.converged else "DISAGREE"
        lines = [f"  {self.deliveries} deliveries later, the replicas {sender}"]
        for index, text in enumerate(self.states):
            lines.append(f"  replica {index}  {text}")
        return lines


def gossip(
    replicas: Sequence[Any],
    merge: Merge,
    serialise: Serialise,
    *,
    seed: int = 7,
    rounds: int = 3,
    duplicates: int = 2,
) -> Gossip:
    """Every replica sends its state to every other one, twice, in a shuffled order."""
    states = list(replicas)
    if len(states) < 2:
        raise ValueError("gossip needs at least two replicas")
    if rounds < 1:
        raise ValueError("gossip needs at least one round")
    if duplicates < 1:
        raise ValueError("deliveries must happen at least once")
    rng = random.Random(seed)
    deliveries = 0
    for _round in range(rounds):
        pairs = [
            (src, dst) for src in range(len(states)) for dst in range(len(states)) if src != dst
        ]
        rng.shuffle(pairs)
        for src, dst in pairs:
            payload = states[src]
            for _copy in range(duplicates):
                states[dst] = merge(states[dst], payload)
                deliveries += 1
    texts = [serialise(state) for state in states]
    return Gossip(states, deliveries, len(set(texts)) == 1, texts)
