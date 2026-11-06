"""The 64 bits, written down.

A snowflake identifier is not an opaque number: it is three fields with sizes
that decide how many workers exist, how many identifiers one worker may issue in
a millisecond, and how long the layout lasts. The sequence is a promise the
clock cannot keep on its own, so every number here is checked at the boundary.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

EPOCH_MS = 1_704_067_200_000  # 2024-01-01T00:00:00Z
TIME_BITS = 41
WORKER_BITS = 10
SEQUENCE_BITS = 12
SEQUENCE_SHIFT = 0
WORKER_SHIFT = SEQUENCE_BITS
TIME_SHIFT = SEQUENCE_BITS + WORKER_BITS

MAX_WORKER = (1 << WORKER_BITS) - 1
MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1
MAX_RELATIVE_MS = (1 << TIME_BITS) - 1
IDS_PER_MS = 1 << SEQUENCE_BITS
WORKERS = 1 << WORKER_BITS
IDS_PER_SECOND_PER_WORKER = IDS_PER_MS * 1_000


class LayoutError(ValueError):
    """A field does not fit the bits it is meant to occupy."""


@dataclass(frozen=True)
class Decoded:
    """The three fields of one identifier, plus the numbers a reader needs."""

    value: int
    relative_ms: int
    worker: int
    sequence: int

    def absolute_ms(self, epoch_ms: int = EPOCH_MS) -> int:
        return epoch_ms + self.relative_ms

    def at(self, epoch_ms: int = EPOCH_MS) -> dt.datetime:
        return dt.datetime.fromtimestamp(self.absolute_ms(epoch_ms) / 1_000, tz=dt.UTC)

    def text(self, epoch_ms: int = EPOCH_MS) -> str:
        return (
            f"{self.value}  at {self.at(epoch_ms).isoformat()}  "
            f"worker {self.worker}  sequence {self.sequence}"
        )

    def as_dict(self, epoch_ms: int = EPOCH_MS) -> dict[str, object]:
        return {
            "value": self.value,
            "at": self.at(epoch_ms).isoformat(),
            "worker": self.worker,
            "sequence": self.sequence,
            "relative_ms": self.relative_ms,
        }


def _check_worker(worker: int) -> int:
    if isinstance(worker, bool) or not isinstance(worker, int):
        raise LayoutError(f"a worker is a whole number, not {worker!r}")
    if not 0 <= worker <= MAX_WORKER:
        raise LayoutError(
            f"worker {worker} does not fit {WORKER_BITS} bits, which hold 0..{MAX_WORKER}"
        )
    return worker


def _check_sequence(sequence: int) -> int:
    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise LayoutError(f"a sequence is a whole number, not {sequence!r}")
    if not 0 <= sequence <= MAX_SEQUENCE:
        raise LayoutError(
            f"sequence {sequence} does not fit {SEQUENCE_BITS} bits, which hold 0..{MAX_SEQUENCE}"
        )
    return sequence


def compose(relative_ms: int, worker: int, sequence: int) -> int:
    """Pack the three fields into one identifier."""
    if isinstance(relative_ms, bool) or not isinstance(relative_ms, int):
        raise LayoutError(f"a timestamp is a whole number of milliseconds, not {relative_ms!r}")
    if relative_ms < 0:
        raise LayoutError("a timestamp before the epoch has no place in the layout")
    if relative_ms > MAX_RELATIVE_MS:
        raise LayoutError(
            f"{relative_ms} ms is past the {TIME_BITS}-bit field; this layout ends after "
            f"{MAX_RELATIVE_MS} ms"
        )
    _check_worker(worker)
    _check_sequence(sequence)
    return (relative_ms << TIME_SHIFT) | (worker << WORKER_SHIFT) | (sequence << SEQUENCE_SHIFT)


def decode(value: int) -> Decoded:
    """Split one identifier back into its fields."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise LayoutError(f"an identifier is a whole number, not {value!r}")
    if value < 0:
        raise LayoutError("an identifier is never negative")
    if value >> 63:
        raise LayoutError("this identifier does not fit 63 bits, so it is not one of ours")
    return Decoded(
        value=value,
        relative_ms=value >> TIME_SHIFT,
        worker=(value >> WORKER_SHIFT) & MAX_WORKER,
        sequence=value & MAX_SEQUENCE,
    )


def years_of_layout() -> float:
    """How long 41 bits of milliseconds last, in Julian years."""
    return MAX_RELATIVE_MS / 1_000 / 60 / 60 / 24 / 365.25


def exhaustion_date(epoch_ms: int = EPOCH_MS) -> dt.datetime:
    return dt.datetime.fromtimestamp((epoch_ms + MAX_RELATIVE_MS) / 1_000, tz=dt.UTC)


def capacity_lines(epoch_ms: int = EPOCH_MS) -> list[str]:
    return [
        f"time         {TIME_BITS} bits = {MAX_RELATIVE_MS} ms = {years_of_layout():.2f} years",
        f"worker       {WORKER_BITS} bits = {WORKERS} workers",
        f"sequence     {SEQUENCE_BITS} bits = {IDS_PER_MS} identifiers per worker per ms",
        f"throughput   {IDS_PER_SECOND_PER_WORKER:,} per second per worker",
        f"layout ends  {exhaustion_date(epoch_ms).isoformat()}",
    ]
