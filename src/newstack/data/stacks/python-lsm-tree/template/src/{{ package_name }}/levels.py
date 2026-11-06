"""Numbered level tables: one frozen file per flush, keys kept sorted.

A level table is the smallest durable promise this project makes: sorted
records, a name that carries its birth order, and a reader that refuses
junk. The oldest invariant in the file: a tombstone outranks the value it
buries, so a merge that sees both keeps neither and reports both.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SUFFIX = ".lsm"
TOMBSTONE_MARK = ""


class LevelError(ValueError):
    """The table on disk is not a table this reader can trust."""


@dataclass(frozen=True)
class MergeReport:
    """What one compaction did: kept, dropped, and how many tables it read."""

    kept: int
    dropped: int
    tables: int
    seq: int


def table_name(seq: int) -> str:
    """The file name carries the birth order: six digits, ascending."""
    if isinstance(seq, bool) or not isinstance(seq, int) or seq < 0:
        raise LevelError("a level sequence is a non-negative integer")
    return f"{seq:06d}{SUFFIX}"


def table_seq(path: Path) -> int:
    """Read the birth order back out of a level table path."""
    try:
        return int(path.stem)
    except ValueError as seen:
        raise LevelError(f"{path.name} is not a numbered level table") from seen


def write_table(directory: Path, seq: int, entries: list[tuple[int, str | None]]) -> Path:
    """Freeze sorted entries into one immutable level table; tombstone is blank."""
    keys = [key for key, _ in entries]
    if keys != sorted(keys) or len(set(keys)) != len(keys):
        raise LevelError("a level table needs sorted, distinct keys")
    path = directory / table_name(seq)
    lines = [f"{key}\t{TOMBSTONE_MARK if value is None else value}" for key, value in entries]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def read_table(path: Path) -> dict[int, str | None]:
    """One read of a level table: newest writes live in the file as it stands."""
    if not path.exists():
        raise LevelError(f"no level table at {path}")
    frozen: dict[int, str | None] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            raise LevelError(f"{path.name} line {number} is not a record")
        try:
            key = int(parts[0])
        except ValueError as seen:
            raise LevelError(f"{path.name} line {number} has no integer key") from seen
        if key in frozen:
            raise LevelError(f"{path.name} line {number} repeats a frozen key")
        frozen[key] = None if parts[1] == TOMBSTONE_MARK else parts[1]
    return frozen


def merge_answers(tables: list[dict[int, str | None]]) -> dict[int, str | None]:
    """The answer a stack of level tables gives, tombstones still standing.

    Tables arrive oldest-first, so the last writer keeps the word and a
    tombstone outranks any value it sits on top of.
    """
    winner: dict[int, str | None] = {}
    for table in tables:
        winner.update(table)
    return winner
