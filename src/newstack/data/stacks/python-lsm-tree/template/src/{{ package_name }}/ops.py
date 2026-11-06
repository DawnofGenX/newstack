"""Workloads: op streams from files or seeds, and the dict they answer to.

A workload is the falsifier. Feed the stream to the table and to a plain
dict, small memtable limit so the table flushes under every keystroke, and
the final answer of each key must equal the dict answer. The file format
is one op per line: ``put N text``, ``del N``, ``get N``.
"""

from __future__ import annotations

import random
from pathlib import Path

from .table import LSMTable

PUT, DELETE, GET = "put", "del", "get"
WORKLOAD_SPAN = (-60, 60)


class OpsError(ValueError):
    """The op stream is not a stream this reader can replay."""


def parse_line(line: str, number: int) -> tuple[str, int, str | None]:
    """One line of an op file, exactly: op, integer key, optional value."""
    words = line.split(None, 2)
    if not words or words[0] not in (PUT, DELETE, GET):
        raise OpsError(f"line {number} opens with no known op")
    try:
        key = int(words[1])
    except (IndexError, ValueError) as seen:
        raise OpsError(f"line {number} has no integer key") from seen
    if words[0] == PUT:
        if len(words) != 3 or not words[2].strip():
            raise OpsError(f"line {number} puts no value")
        return (PUT, key, words[2].strip())
    if len(words) != 2:
        raise OpsError(f"line {number} asks {words[0]} with trailing junk")
    return (words[0], key, None)


def load_ops(path: str | Path) -> list[tuple[str, int, str | None]]:
    """An op file: one op per line, blanks and # comments skipped."""
    stream: list[tuple[str, int, str | None]] = []
    for number, raw in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        stream.append(parse_line(line, number))
    if not stream:
        raise OpsError("an op file of nothing replays nothing")
    return stream


def workload(
    ops: int, seed: int, low: int = WORKLOAD_SPAN[0], high: int = WORKLOAD_SPAN[1]
) -> list[tuple[str, int, str | None]]:
    """A seeded write/delete/read mix; same seed, same stream, every run."""
    if isinstance(ops, bool) or not isinstance(ops, int) or ops < 1:
        raise OpsError("a workload counts one or more ops")
    if low >= high:
        raise OpsError("a workload span needs low below high")
    rng = random.Random(seed)
    stream: list[tuple[str, int, str | None]] = []
    for _ in range(ops):
        roll = rng.random()
        key = rng.randrange(low, high)
        if roll < 0.5:
            stream.append((PUT, key, f"v{rng.randrange(1000):03d}"))
        elif roll < 0.75:
            stream.append((DELETE, key, None))
        else:
            stream.append((GET, key, None))
    return stream


def replay_dict(stream: list[tuple[str, int, str | None]]) -> dict[int, str]:
    """What a plain dict answers after the same stream: the ground truth."""
    shelf: dict[int, str] = {}
    for op, key, value in stream:
        if op == PUT:
            assert value is not None
            shelf[key] = value
        elif op == DELETE:
            shelf.pop(key, None)
    return shelf


def replay_table(
    stream: list[tuple[str, int, str | None]], directory: str | Path, limit: int
) -> tuple[LSMTable, dict[int, str]]:
    """Replay the stream on a flushed-every-second table; report the answers."""
    table = LSMTable(directory, memtable_limit=limit)
    for op, key, value in stream:
        if op == PUT:
            assert value is not None
            table.put(key, value)
        elif op == DELETE:
            table.delete(key)
    return table, dict(table.items())
