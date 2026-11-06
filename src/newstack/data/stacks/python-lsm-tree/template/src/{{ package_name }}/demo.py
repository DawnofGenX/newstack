"""Six stories about a table that answers newest-level-first.

Nothing here is a picture of the algorithm; every claim is a comparison
the demo computes against a plain dict, and `stories` reports whether all
of them held under a memtable small enough to flush under every keystroke.
"""

from __future__ import annotations

from tempfile import TemporaryDirectory

from .ops import replay_dict, replay_table, workload
from .table import LSMTable

__all__ = ["Story", "render_stories", "stories"]

WORKLOAD_OPS = 240
WORKLOAD_SEED = 7
TIGHT_LIMIT = 3


class Story:
    """One story: a claim, the lines that argue for it, and the checks that hold it up."""

    def __init__(self, title: str) -> None:
        self.title = title
        self.lines: list[str] = []
        self.checks: list[tuple[str, bool]] = []

    def say(self, text: str) -> None:
        self.lines.append(f"  {text}")

    def require(self, claim: str, held: bool) -> None:
        self.checks.append((claim, bool(held)))
        mark = "ok  " if held else "FAIL"
        self.lines.append(f"  {mark} {claim}")

    @property
    def held(self) -> bool:
        return all(held for _, held in self.checks) and bool(self.checks)

    def render(self) -> list[str]:
        return [self.title, *self.lines]


def _tight_workload() -> list[tuple[str, int, str | None]]:
    return workload(WORKLOAD_OPS, seed=WORKLOAD_SEED)


def _story_flood() -> Story:
    story = Story("1. a tight memtable flushes under every few writes")
    stream = _tight_workload()
    with TemporaryDirectory() as room:
        table, _answers = replay_table(stream, room, limit=TIGHT_LIMIT)
        story.say(f"flushes: {table.flushes}, level tables: {table.level_count()}")
        story.require("the flood forced many flushes", table.flushes >= 10)
    return story


def _story_dict() -> Story:
    story = Story("2. the table answers exactly what the dict answers")
    stream = _tight_workload()
    with TemporaryDirectory() as room:
        _, answers = replay_table(stream, room, limit=TIGHT_LIMIT)
        story.require("every final answer equals the dict answer", answers == replay_dict(stream))
    return story


def _story_tombstone() -> Story:
    story = Story("3. a tombstone hides the value across the flush boundary")
    with TemporaryDirectory() as room:
        table = LSMTable(room, memtable_limit=2)
        table.put(9, "buried")
        table.flush()
        table.delete(9)
        story.say("put 9 buried, flushed, deleted, never re-flushed")
        story.require("the tombstone outranks the older level", table.get(9) is None)
        table.flush()
        story.require("and still outranks it once frozen", table.get(9) is None)
    return story


def _story_iterate() -> Story:
    story = Story("4. iteration is sorted-unique across every level")
    stream = _tight_workload()
    with TemporaryDirectory() as room:
        table, answers = replay_table(stream, room, limit=TIGHT_LIMIT)
        keys = table.keys()
        story.require("the walk is sorted", keys == sorted(keys))
        story.require("the walk has no repeats", len(set(keys)) == len(keys))
        story.require("the walk is the dict keys", keys == sorted(answers))
    return story


def _story_compact() -> Story:
    story = Story("5. compaction merges the levels and retires tombstones")
    stream = _tight_workload()
    with TemporaryDirectory() as room:
        table, answers = replay_table(stream, room, limit=TIGHT_LIMIT)
        before = table.level_count()
        report = table.compact()
        story.say(f"{before} level tables merged: kept {report.kept}, dropped {report.dropped}")
        story.require("one table stands after the merge", table.level_count() == 1)
        story.require("the answers survive the merge", dict(table.items()) == answers)
        story.require("no tombstone survived", report.dropped > 0)
    return story


def _story_reopen() -> Story:
    story = Story("6. reopen-from-disk reads the same table back")
    stream = _tight_workload()
    with TemporaryDirectory() as room:
        table, answers = replay_table(stream, room, limit=TIGHT_LIMIT)
        table.flush()
        reopened = LSMTable(room, memtable_limit=TIGHT_LIMIT)
        story.require("the reopened table answers identically", dict(reopened.items()) == answers)
        story.require("and the level count came off the disk", reopened.level_count() > 1)
    return story


def stories() -> list[Story]:
    return [
        _story_flood(),
        _story_dict(),
        _story_tombstone(),
        _story_iterate(),
        _story_compact(),
        _story_reopen(),
    ]


def render_stories() -> tuple[str, bool]:
    """The demo as text plus whether every story held."""
    told = stories()
    lines: list[str] = []
    for story in told:
        lines.extend(story.render())
        lines.append("")
    held = all(story.held for story in told)
    return "\n".join(lines).rstrip("\n"), held
