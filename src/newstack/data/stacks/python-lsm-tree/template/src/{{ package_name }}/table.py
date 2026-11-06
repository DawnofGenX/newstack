"""A log-structured merge table over integer keys and string values.

Writes land in a sorted in-memory memtable and stay there until a flush
freezes them into a numbered level table on disk. A read checks the
memtable first, then falls through the level tables newest first and stops
at the first table that knows the key — the rule the whole table lives by:
a tombstone outranks the value it buries. Internally a tombstone is the
same ``None`` a missing answer carries, in the memtable, in a level map,
and in a table file. Compaction merges every level table into one sorted
table and retires the tombstones, because after a full merge nothing
older is left to hide.
"""

from __future__ import annotations

from pathlib import Path

from .levels import MergeReport, merge_answers, read_table, table_seq, write_table

MEMTABLE_LIMIT = 8


class TableError(ValueError):
    """The caller asked something this table refuses to remember."""


def _demand(key: object, value: object) -> None:
    if isinstance(key, bool) or not isinstance(key, int):
        raise TableError("a key is an integer")
    if not isinstance(value, str):
        raise TableError("a value is a string")


class LSMTable:
    """A memtable over numbered level tables, answering newest level first."""

    def __init__(self, directory: str | Path, memtable_limit: int = MEMTABLE_LIMIT) -> None:
        if isinstance(memtable_limit, bool) or not isinstance(memtable_limit, int):
            raise TableError("a memtable limit is an integer")
        if memtable_limit < 1:
            raise TableError("a memtable limit is one or more")
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.memtable_limit = memtable_limit
        self.memtable: dict[int, str | None] = {}
        self.levels: dict[int, dict[int, str | None]] = {}
        self.flushes = 0
        self._seq = 0
        self._adopt_existing()

    def _adopt_existing(self) -> None:
        """Reopen is a read: the directory already holds the whole history."""
        found: dict[int, dict[int, str | None]] = {}
        for path in sorted(self.directory.glob("*.lsm")):
            found[table_seq(path)] = read_table(path)
        self.levels = found
        self._seq = max(found, default=-1) + 1

    def put(self, key: int, value: str) -> None:
        """The newest answer for a key is whatever this call last said."""
        _demand(key, value)
        self.memtable[key] = value
        if len(self.memtable) >= self.memtable_limit:
            self.flush()

    def delete(self, key: int) -> None:
        """A tombstone is a write: it answers absent until something newer."""
        if isinstance(key, bool) or not isinstance(key, int):
            raise TableError("a key is an integer")
        self.memtable[key] = None
        if len(self.memtable) >= self.memtable_limit:
            self.flush()

    def get(self, key: int) -> str | None:
        """Memtable first, then level tables newest first; tombstone is absent."""
        if isinstance(key, bool) or not isinstance(key, int):
            raise TableError("a key is an integer")
        if key in self.memtable:
            return self.memtable[key]
        for seq in sorted(self.levels, reverse=True):
            if key in self.levels[seq]:
                return self.levels[seq][key]
        return None

    def items(self) -> list[tuple[int, str]]:
        """Sorted unique keys across every level; tombstones answer absent."""
        answers = merge_answers(self._stack())
        return [(key, value) for key, value in sorted(answers.items()) if value is not None]

    def keys(self) -> list[int]:
        return [key for key, _ in self.items()]

    def flush(self) -> int | None:
        """Freeze the memtable into the next numbered level table."""
        if not self.memtable:
            return None
        write_table(self.directory, self._seq, sorted(self.memtable.items()))
        self.levels[self._seq] = dict(self.memtable)
        self._seq += 1
        self.flushes += 1
        self.memtable.clear()
        return self._seq - 1

    def compact(self) -> MergeReport:
        """Merge every level table into one; tombstones retire with it."""
        if not self.levels:
            return MergeReport(kept=0, dropped=0, tables=0, seq=-1)
        answers = merge_answers([self.levels[seq] for seq in sorted(self.levels)])
        survived: dict[int, str | None] = {
            key: value for key, value in answers.items() if value is not None
        }
        seq = self._seq
        write_table(self.directory, seq, sorted(survived.items()))
        for old in sorted(self.levels):
            (self.directory / f"{old:06d}.lsm").unlink(missing_ok=True)
        dropped = len(answers) - len(survived)
        self.levels = {seq: survived}
        self._seq = seq + 1
        return MergeReport(kept=len(survived), dropped=dropped, tables=len(answers), seq=seq)

    def level_count(self) -> int:
        """On-disk level tables now standing, oldest order."""
        return len(self.levels)

    def _stack(self) -> list[dict[int, str | None]]:
        """Every level oldest-first so a dict update leaves the newest word."""
        return [self.levels[seq] for seq in sorted(self.levels)] + [dict(self.memtable)]
