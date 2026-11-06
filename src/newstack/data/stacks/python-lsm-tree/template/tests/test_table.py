from __future__ import annotations

from pathlib import Path

import pytest

from {{ package_name }}.ops import DELETE, PUT, replay_dict, workload
from {{ package_name }}.table import LSMTable, TableError

SEEDS = (7, 23, 101)


def drain(table: LSMTable, stream: list[tuple[str, int, str | None]]) -> None:
    for op, key, value in stream:
        if op == PUT:
            assert value is not None
            table.put(key, value)
        elif op == DELETE:
            table.delete(key)


def filled(directory: Path, limit: int = 4) -> LSMTable:
    table = LSMTable(directory, memtable_limit=limit)
    for key in (-9, 3, 42):
        table.put(key, f"v{key}")
    return table


def test_put_then_get_answers_the_value(tmp_path: Path) -> None:
    table = LSMTable(tmp_path)
    table.put(12, "alpha")
    assert table.get(12) == "alpha"
    assert table.get(13) is None


def test_the_newest_write_owns_the_answer(tmp_path: Path) -> None:
    table = filled(tmp_path)
    table.put(3, "second")
    assert table.get(3) == "second"


def test_delete_answers_absent_until_a_newer_write(tmp_path: Path) -> None:
    table = filled(tmp_path)
    table.delete(3)
    assert table.get(3) is None
    table.put(3, "reclaimed")
    assert table.get(3) == "reclaimed"


def test_a_small_limit_flushes_under_the_workload(tmp_path: Path) -> None:
    table = LSMTable(tmp_path, memtable_limit=2)
    drain(table, workload(40, seed=7))
    assert table.flushes >= 5
    assert table.level_count() >= 5


@pytest.mark.parametrize("seed", SEEDS)
def test_every_seed_answers_exactly_what_the_dict_answers(
    tmp_path: Path, seed: int
) -> None:
    stream = workload(160, seed=seed)
    for limit in (1, 3):
        table = LSMTable(tmp_path / f"table-{seed}-{limit}", memtable_limit=limit)
        drain(table, stream)
        assert dict(table.items()) == replay_dict(stream)


@pytest.mark.parametrize("seed", SEEDS)
def test_iteration_is_sorted_unique_across_levels(tmp_path: Path, seed: int) -> None:
    table = LSMTable(tmp_path, memtable_limit=2)
    drain(table, workload(120, seed=seed))
    table.flush()
    keys = table.keys()
    assert keys == sorted(keys)
    assert len(set(keys)) == len(keys)
    assert keys == sorted(replay_dict(workload(120, seed=seed)))


def test_reads_fall_through_the_levels_newest_first(tmp_path: Path) -> None:
    table = LSMTable(tmp_path, memtable_limit=2)
    table.put(5, "oldest")
    table.flush()
    table.put(7, "older")
    table.flush()
    assert table.get(5) == "oldest"
    assert table.get(7) == "older"
    table.put(5, "newest")
    assert table.get(5) == "newest"


def test_a_tombstone_outranks_the_value_it_buries(tmp_path: Path) -> None:
    table = LSMTable(tmp_path, memtable_limit=6)
    table.put(11, "buried")
    table.flush()
    table.delete(11)
    assert table.get(11) is None
    table.flush()
    assert table.get(11) is None
    assert (11, "buried") not in table.items()
    table.put(11, "back")
    assert table.get(11) == "back"


def test_compaction_merges_one_table_and_keeps_answers(tmp_path: Path) -> None:
    table = LSMTable(tmp_path, memtable_limit=2)
    drain(table, workload(120, seed=17))
    table.flush()
    answers = dict(table.items())
    report = table.compact()
    assert table.level_count() == 1
    assert dict(table.items()) == answers
    assert report.tables >= 2


def test_compaction_leaves_no_tombstone_on_disk(tmp_path: Path) -> None:
    table = LSMTable(tmp_path, memtable_limit=6)
    table.put(1, "kept")
    table.delete(2)
    table.flush()
    table.compact()
    standing = list(tmp_path.glob("*.lsm"))
    assert len(standing) == 1
    assert not any(line.endswith("\t") for line in standing[0].read_text().splitlines())


def test_reopen_from_disk_reads_the_identical_table(tmp_path: Path) -> None:
    table = LSMTable(tmp_path, memtable_limit=3)
    stream = workload(90, seed=53)
    drain(table, stream)
    table.flush()
    answers = dict(table.items())
    reopened = LSMTable(tmp_path, memtable_limit=3)
    assert dict(reopened.items()) == answers
    for key in list(answers)[:8]:
        assert reopened.get(key) == answers[key]


def test_a_flush_of_nothing_adds_no_level(tmp_path: Path) -> None:
    table = LSMTable(tmp_path)
    assert table.flush() is None
    assert table.level_count() == 0


def test_the_table_refuses_what_it_cannot_remember(tmp_path: Path) -> None:
    table = LSMTable(tmp_path)
    with pytest.raises(TableError):
        LSMTable(tmp_path, memtable_limit=0)
    with pytest.raises(TableError):
        table.put("one", "v")  # type: ignore[arg-type]
    with pytest.raises(TableError):
        table.put(1, 2)  # type: ignore[arg-type]
    with pytest.raises(TableError):
        table.delete(True)
