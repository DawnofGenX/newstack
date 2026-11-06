"""A history of register operations, and the rules that make one well formed.

Times are integers on a single clock. An operation invokes at ``start`` and
responds at ``end``, so ``[start, end)`` is the interval in which it took effect.
Two operations that touch at one instant are treated as concurrent: nothing in
the history says which of the two events happened first, and a checker that
guesses would be checking its own guess.
"""

from __future__ import annotations

import itertools
import json
from dataclasses import dataclass
from pathlib import Path

READ = "read"
WRITE = "write"
KINDS = (READ, WRITE)
KEYS = ("client", "op", "value", "start", "end")
HEADER_KEY = "initial"


class HistoryError(ValueError):
    """A history could not be read, or it does not describe a register."""


def _whole(payload: dict[str, object], key: str, line: int) -> int:
    value = payload[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise HistoryError(f"line {line}: '{key}' must be a whole number, not {value!r}")
    return value


@dataclass(frozen=True)
class Operation:
    """One operation, with the value it wrote or the value it read back."""

    client: int
    kind: str
    value: int
    start: int
    end: int
    line: int = 0

    def text(self) -> str:
        return f"client {self.client} {self.kind} {self.value} [{self.start}, {self.end})"

    @property
    def duration(self) -> int:
        return self.end - self.start

    def same_interval(self, other: Operation) -> bool:
        return (self.start, self.end) == (other.start, other.end)

    def precedes(self, other: Operation) -> bool:
        """Real-time order: this operation responded before the other invoked."""
        return self.end < other.start

    def overlaps(self, other: Operation) -> bool:
        return not (self.end < other.start or other.end < self.start)


def parse_operation(payload: dict[str, object], line: int) -> Operation:
    if HEADER_KEY in payload:
        raise HistoryError(f"line {line}: a header line cannot also be an operation")
    unknown = sorted(set(payload) - set(KEYS))
    if unknown:
        raise HistoryError(
            f"line {line}: unknown key {unknown[0]!r}; an operation has {', '.join(KEYS)}"
        )
    missing = [key for key in KEYS if key not in payload]
    if missing:
        raise HistoryError(
            f"line {line}: missing {missing[0]!r}; an operation has {', '.join(KEYS)}"
        )
    kind = payload["op"]
    if kind not in KINDS:
        raise HistoryError(f"line {line}: 'op' must be one of {', '.join(KINDS)}, not {kind!r}")
    client = _whole(payload, "client", line)
    if client < 0:
        raise HistoryError(f"line {line}: a client number cannot be negative")
    value = _whole(payload, "value", line)
    start = _whole(payload, "start", line)
    end = _whole(payload, "end", line)
    if start < 0:
        raise HistoryError(f"line {line}: a time cannot be negative")
    if end < start:
        raise HistoryError(
            f"line {line}: the response at {end} comes before the invocation at {start}"
        )
    return Operation(client=client, kind=str(kind), value=value, start=start, end=end, line=line)


@dataclass(frozen=True)
class History:
    """Operations in the order they appear in the file, plus the initial value."""

    operations: tuple[Operation, ...] = ()
    initial: int = 0
    source: str = "<memory>"

    def __len__(self) -> int:
        return len(self.operations)

    @property
    def clients(self) -> tuple[int, ...]:
        return tuple(sorted({op.client for op in self.operations}))

    def of_client(self, client: int) -> tuple[Operation, ...]:
        return tuple(op for op in self.operations if op.client == client)

    @property
    def span(self) -> int:
        if not self.operations:
            return 0
        return max(op.end for op in self.operations) - min(op.start for op in self.operations)

    def restricted(self, keep: list[int] | tuple[int, ...]) -> History:
        """The same clients, programs and times, with only the operations asked for."""
        wanted = set(keep)
        kept = tuple(op for index, op in enumerate(self.operations) if index in wanted)
        return History(operations=kept, initial=self.initial, source=self.source)

    def lines(self) -> list[str]:
        lines = [f"initial    {self.initial}", f"operations {len(self.operations)}"]
        for index, op in enumerate(self.operations, start=1):
            lines.append(f"{index:>3}  {op.text()}")
        return lines


def parse_lines(lines: list[str], *, source: str = "<memory>") -> History:
    operations: list[Operation] = []
    initial = 0
    seen_header = False
    for number, raw in enumerate(lines, start=1):
        text = raw.strip()
        if not text or text.startswith("#"):
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            raise HistoryError(f"line {number} is not JSON: {error.msg}") from None
        if not isinstance(payload, dict):
            raise HistoryError(f"line {number} must be a JSON object, not {type(payload).__name__}")
        if HEADER_KEY in payload:
            if seen_header:
                raise HistoryError(f"line {number}: a second header line repeats the initial value")
            if set(payload) != {HEADER_KEY}:
                raise HistoryError(
                    f"line {number}: a header line holds only '{HEADER_KEY}', not {sorted(payload)}"
                )
            initial = _whole(payload, HEADER_KEY, number)
            seen_header = True
            continue
        operations.append(parse_operation(payload, number))
    history = History(operations=tuple(operations), initial=initial, source=source)
    _check_programs(history)
    return history


def _check_programs(history: History) -> None:
    """Every client's operations must be ordered by time, since a client is one programme."""
    for client in history.clients:
        ops = history.of_client(client)
        for before, after in itertools.pairwise(ops):
            if before.end > after.start:
                raise HistoryError(
                    f"client {client} has two operations that overlap in time "
                    f"({before.text()} then {after.text()}), so their order is not defined"
                )


def load(path: Path) -> History:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise HistoryError(f"no such history: {path}") from None
    except OSError as error:
        raise HistoryError(f"cannot read {path}: {error.strerror}") from None
    return parse_lines(text.splitlines(), source=str(path))
