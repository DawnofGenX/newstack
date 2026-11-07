"""The reference drain: a stdlib deque with no cursor of its own.

The deque with a fixed `maxlen` drops the oldest value on an
over-capacity append all by itself, so it is the oracle the ring is
checked against, not a second copy of the ring's logic. Every order
the buffer returns must be the identical answer the deque gives.
"""

from __future__ import annotations

from collections import deque


def reference_drain(capacity: int, values: list[int]) -> list[int]:
    """The values the deque would hand back after the pushes, in order."""
    seats: deque[int] = deque(maxlen=capacity)
    for value in values:
        seats.append(value)
    return list(seats)


def storm_reference(
    capacity: int, operations: list[tuple[str, int | None]]
) -> list[int]:
    """The drains a deque answers through a push/pop/peek/drain storm.

    Returns the concatenated drains and pops the reference sequence
    hands back, step for step with the ring's own answers.
    """
    seats: deque[int] = deque(maxlen=capacity)
    answers: list[int] = []
    for verb, value in operations:
        if verb == "push":
            seats.append(int(value))  # type: ignore[arg-type]
        elif verb == "pop" and seats:
            answers.append(seats.popleft())
        elif verb == "drain":
            answers.extend(seats)
            seats.clear()
    return answers


def drop_oldest_view(capacity: int, values: list[int]) -> tuple[int, ...]:
    """The visible sequence the deque shows after the pushes, no pops."""
    seats: deque[int] = deque(maxlen=capacity)
    for value in values:
        seats.append(value)
    return tuple(seats)
