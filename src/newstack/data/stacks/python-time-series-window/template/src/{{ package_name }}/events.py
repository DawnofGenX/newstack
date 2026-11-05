"""Events, and the one thing a time series file must tell you: when it happened.

Timestamps are integer microseconds since the epoch. Floats lose microseconds at
2026 magnitudes, and a window boundary decided by a rounding error is a boundary
two readers disagree about.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

US = 1_000_000


class EventError(ValueError):
    """An event that cannot be read as a fact about time."""


def to_us(text: str) -> int:
    """Parse an ISO timestamp that carries an offset, or an integer microsecond count."""
    stripped = text.strip()
    if stripped.lstrip("-").isdigit():
        return int(stripped)
    try:
        moment = datetime.fromisoformat(stripped)
    except ValueError as error:
        raise EventError(f"{text!r} is not an ISO timestamp: {error}") from None
    if moment.tzinfo is None:
        raise EventError(
            f"{text!r} has no UTC offset; a naive timestamp is a local guess, and every "
            "window it lands in is ambiguous by up to a day"
        )
    return int(moment.timestamp() * US)


def to_iso(t_us: int) -> str:
    """Render microseconds exactly, and print whole seconds without noise.

    Dividing by US in a float loses the last microsecond at 2026 magnitudes, so
    the split happens in integers. UTC prints as `Z`, the way log files do.
    """
    seconds, micro = divmod(t_us, US)
    moment = datetime.fromtimestamp(seconds, UTC).replace(microsecond=micro)
    timespec = "microseconds" if micro else "seconds"
    return moment.isoformat(timespec=timespec).replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class Event:
    t_us: int
    value: float | None = None

    def __post_init__(self) -> None:
        if isinstance(self.t_us, bool) or not isinstance(self.t_us, int):
            raise EventError(f"t_us must be an integer microsecond count, got {self.t_us!r}")
        if isinstance(self.value, bool) or (
            self.value is not None and not isinstance(self.value, (int, float))
        ):
            raise EventError(f"value must be a number or null, got {self.value!r}")

    @property
    def at(self) -> str:
        return to_iso(self.t_us)


def parse_event(payload: object, *, where: str) -> Event:
    if not isinstance(payload, dict):
        raise EventError(f"{where}: an event must be a JSON object")
    if "t" not in payload:
        raise EventError(f"{where}: an event needs a 't' timestamp")
    stamp = payload["t"]
    if isinstance(stamp, bool) or not isinstance(stamp, (str, int)):
        raise EventError(f"{where}: 't' must be an ISO string or an integer, got {stamp!r}")
    t_us = to_us(stamp) if isinstance(stamp, str) else stamp
    value = payload.get("value")
    if isinstance(value, bool):
        raise EventError(f"{where}: a boolean is not a measurement")
    return Event(t_us=t_us, value=value)


def load(path: Path) -> list[Event]:
    """Read a JSONL file in arrival order. Order is data, so it is never sorted."""
    try:
        text = path.read_text()
    except OSError as error:
        raise EventError(f"cannot read {path}: {error}") from None
    events: list[Event] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as error:
            raise EventError(f"{path}: line {number} is not JSON: {error}") from None
        events.append(parse_event(payload, where=f"{path}: line {number}"))
    if not events:
        raise EventError(f"{path} holds no events")
    return events
