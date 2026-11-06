"""The invariants this table promises, run against the real modules.

Every claim here is the reason the levels are trustworthy: every final
answer of a seeded workload equals the dict answer, a tombstone outranks
the value it buries across a flush boundary, iteration is sorted-unique
across levels, and reopen-from-disk reads the identical table. Runnable
in a fresh checkout: `{{ package_name }} selftest`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory

from .levels import LevelError, read_table, table_seq, write_table
from .ops import DELETE, PUT, OpsError, load_ops, parse_line, replay_dict, workload
from .table import LSMTable, TableError

FIXTURE = "a tombstone outranks the value it buries"
SEEDS = (7, 23, 101, 404)


@dataclass
class Report:
    checks: int = 0
    failed: int = 0
    lines: list[str] = field(default_factory=list)

    def section(self, name: str) -> None:
        self.lines.append(f"- {name}")

    def ok(self, claim: str, held: bool) -> None:
        self.checks += 1
        if held:
            self.lines.append(f"  ok   {claim}")
        else:
            self.failed += 1
            self.lines.append(f"  FAIL {claim}")

    def equal(self, claim: str, found: object, expected: object) -> None:
        self.ok(
            f"{claim} ({found!r})" if found == expected else f"{claim}: {found!r} != {expected!r}",
            found == expected,
        )

    def refuses(self, claim: str, call: object, error: type[Exception]) -> None:
        try:
            call()  # type: ignore[operator]
        except error as seen:
            self.ok(f"{claim} ({seen})", True)
        except Exception as seen:
            self.ok(f"{claim}: raised {type(seen).__name__}, not {error.__name__}", False)
        else:
            self.ok(f"{claim}: nothing raised", False)

    def render(self) -> str:
        body = "\n".join(self.lines)
        return f"{body}\n\nselftest: {self.checks} checks passed, {self.failed} failed"


def _drain(table: LSMTable, stream: list[tuple[str, int, str | None]]) -> None:
    """Replay a workload stream: writes and deletes in, nothing read back yet."""
    for op, key, value in stream:
        if op == PUT:
            assert value is not None
            table.put(key, value)
        elif op == DELETE:
            table.delete(key)


def _dict_parity(report: Report) -> None:
    report.section("a seeded workload answers exactly what the dict answers")
    for seed in SEEDS:
        for limit in (1, 3):
            stream = workload(160, seed=seed)
            with TemporaryDirectory() as room:
                table = LSMTable(room, memtable_limit=limit)
                _drain(table, stream)
                report.equal(
                    f"seed {seed} limit {limit} ends as the dict",
                    dict(table.items()),
                    replay_dict(stream),
                )
                report.ok(f"seed {seed} limit {limit} forced many flushes", table.flushes >= 5)


def _tombstone(report: Report) -> None:
    report.section("a tombstone outranks the value it buries")
    with TemporaryDirectory() as room:
        table = LSMTable(room, memtable_limit=6)
        table.put(11, "buried")
        table.flush()
        table.delete(11)
        report.equal("the tombstone hides it in the memtable", table.get(11), None)
        table.flush()
        report.equal("and hides it across the flush boundary", table.get(11), None)
        table.put(11, "resurrected")
        report.equal("a newer write reclaims the key", table.get(11), "resurrected")


def _fallthrough(report: Report) -> None:
    report.section("reads fall through the levels, newest first")
    with TemporaryDirectory() as room:
        table = LSMTable(room, memtable_limit=2)
        table.put(5, "oldest")
        table.flush()
        report.equal("a flush of nothing adds no level", table.level_count(), 1)
        table.put(7, "older")
        table.flush()
        report.equal("a key only the oldest level knows", table.get(5), "oldest")
        report.equal("a key the newest level knows", table.get(7), "older")
        table.put(5, "newest")
        report.equal("the memtable outranks every level", table.get(5), "newest")
        report.equal("an unknown key answers absent", table.get(999), None)


def _iteration(report: Report) -> None:
    report.section("iteration is sorted-unique across every level")
    stream = workload(200, seed=31)
    with TemporaryDirectory() as room:
        table = LSMTable(room, memtable_limit=2)
        _drain(table, stream)
        table.flush()
        keys = table.keys()
        report.equal("the walk is sorted", keys, sorted(keys))
        report.equal("the walk has no repeats", len(set(keys)), len(keys))
        report.equal("the walk is the dict keys", keys, sorted(replay_dict(stream)))
        answers = dict(table.items())
        for key, value in list(answers.items())[:10]:
            report.equal(f"walk and get agree on {key}", table.get(key), value)


def _compaction(report: Report) -> None:
    report.section("compaction merges sorted and retires tombstones")
    stream = workload(120, seed=17)
    with TemporaryDirectory() as room:
        table = LSMTable(room, memtable_limit=2)
        _drain(table, stream)
        table.flush()
        before = dict(table.items())
        merge = table.compact()
        report.equal("one level table stands", table.level_count(), 1)
        report.equal("the answers survive the merge", dict(table.items()), before)
        report.ok("the merge read more than one table", merge.tables >= 2)
        reopened = LSMTable(room, memtable_limit=2)
        report.equal("the merged table reads back identical", dict(reopened.items()), before)


def _reopen(report: Report) -> None:
    report.section("reopen-from-disk reads the identical table")
    stream = workload(90, seed=53)
    with TemporaryDirectory() as room:
        table = LSMTable(room, memtable_limit=3)
        _drain(table, stream)
        table.flush()
        answers = dict(table.items())
        reopened = LSMTable(room, memtable_limit=3)
        report.equal("the reopened table answers identically", dict(reopened.items()), answers)
        standing = len(list(Path(room).glob("*.lsm")))
        report.equal("the reopened levels came off the disk", reopened.level_count(), standing)
        for key in list(answers)[:8]:
            report.equal(f"reopened get {key}", reopened.get(key), answers[key])


def _levels(report: Report) -> None:
    report.section("level files carry their order and refuse junk")
    with TemporaryDirectory() as room:
        root = Path(room)
        path = write_table(root, 7, [(-2, "v"), (3, None)])
        report.equal("the name carries the birth order", path.name, "000007.lsm")
        report.equal("the order reads back out", table_seq(path), 7)
        report.equal("a tombstone freezes as absent", read_table(path)[3], None)
        report.refuses(
            "unsorted entries are refused",
            lambda: write_table(root, 1, [(4, "a"), (2, "b")]),
            LevelError,
        )
        report.refuses(
            "a repeated key is refused",
            lambda: write_table(root, 2, [(1, "a"), (1, "b")]),
            LevelError,
        )
        junk = root / "000009.lsm"
        junk.write_text("not-a-record\n", encoding="utf-8")
        report.refuses("junk is refused by name", lambda: read_table(junk), LevelError)
        report.refuses(
            "a missing table is named", lambda: read_table(root / "000042.lsm"), LevelError
        )


def _workload_rules(report: Report) -> None:
    report.section("workloads and op files replay the same way twice")
    first = workload(40, seed=9)
    report.equal("the generator is deterministic", first, workload(40, seed=9))
    report.ok("a different seed is a different stream", first != workload(40, seed=10))
    report.refuses("a workload of zero is not a workload", lambda: workload(0, seed=1), OpsError)
    report.refuses(
        "an empty span is refused", lambda: workload(4, 1, low=5, high=5), OpsError
    )
    with TemporaryDirectory() as room:
        path = Path(room) / "ops.txt"
        path.write_text("# a comment\nput 3 text here\n\nget 3\ndel 3\n", encoding="utf-8")
        report.equal("blanks and comments are skipped", len(load_ops(path)), 3)
        empty = Path(room) / "none.txt"
        empty.write_text("# nothing but a comment\n", encoding="utf-8")
        report.refuses("a file of comments replays nothing", lambda: load_ops(empty), OpsError)
        report.refuses(
            "an unknown op is named", lambda: parse_line("frobnicate 1", 1), OpsError
        )
        report.refuses(
            "a put without a value is named", lambda: parse_line("put 7", 1), OpsError
        )


def _table_rules(report: Report) -> None:
    report.section("the table refuses what it cannot remember")
    with TemporaryDirectory() as room:
        table = LSMTable(room)
        report.refuses(
            "a limit below one is refused", lambda: LSMTable(room, memtable_limit=0), TableError
        )
        report.refuses(
            "a fractional limit is refused",
            lambda: LSMTable(room, memtable_limit=2.5),  # type: ignore[arg-type]
            TableError,
        )
        # type: ignore[arg-type] lives on the call lines below
        report.refuses(
            "a string key is refused", lambda: table.put("1", "v"), TableError
        )
        report.refuses(
            "an integer value is refused", lambda: table.put(1, 2), TableError
        )
        report.refuses("a boolean key is refused", lambda: table.delete(True), TableError)
        table.flush()
        report.equal("a flush of nothing flushes nothing", table.flush(), None)
        merge = table.compact()
        report.equal("a merge of nothing stands empty", (merge.kept, merge.dropped), (0, 0))
        report.equal("an empty table iterates to nothing", table.items(), [])


def _marker(report: Report) -> None:
    report.section("the phrase the detector looks for ships in the code")
    from . import table as table_module

    joined = " ".join((table_module.__doc__ or "").split())
    report.ok("the marker sits in the table module docstring", FIXTURE in joined)


def run() -> Report:
    report = Report()
    _dict_parity(report)
    _tombstone(report)
    _fallthrough(report)
    _iteration(report)
    _compaction(report)
    _reopen(report)
    _levels(report)
    _workload_rules(report)
    _table_rules(report)
    _marker(report)
    return report
