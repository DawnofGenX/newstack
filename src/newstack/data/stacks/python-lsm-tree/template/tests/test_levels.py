from __future__ import annotations

from pathlib import Path

import pytest

from {{ package_name }}.levels import (
    LevelError,
    merge_answers,
    read_table,
    table_seq,
    write_table,
)


def test_the_name_carries_the_birth_order() -> None:
    assert table_seq(Path("inside/000042.lsm")) == 42


def test_a_junk_name_is_not_a_sequence() -> None:
    with pytest.raises(LevelError):
        table_seq(Path("notes.txt"))


def test_a_frozen_table_reads_back_what_was_written(
    tmp_path: Path,
) -> None:
    entries = [(-3, None), (0, "v0"), (9, "v9")]
    frozen = write_table(tmp_path, 7, entries)
    assert frozen.name == "000007.lsm"
    assert read_table(frozen) == dict(entries)


def test_a_tombstone_freezes_as_an_empty_value(tmp_path: Path) -> None:
    frozen = write_table(tmp_path, 1, [(4, None)])
    assert frozen.read_text(encoding="utf-8") == "4\t\n"
    assert read_table(frozen)[4] is None


def test_unsorted_or_repeated_entries_are_refused(tmp_path: Path) -> None:
    with pytest.raises(LevelError):
        write_table(tmp_path, 1, [(4, "a"), (2, "b")])
    with pytest.raises(LevelError):
        write_table(tmp_path, 2, [(1, "a"), (1, "b")])


def test_junk_and_missing_files_are_refused(tmp_path: Path) -> None:
    junk = tmp_path / "000009.lsm"
    junk.write_text("no tab here\n", encoding="utf-8")
    with pytest.raises(LevelError):
        read_table(junk)
    with pytest.raises(LevelError):
        read_table(tmp_path / "000042.lsm")


def test_merge_answers_leaves_the_newest_word() -> None:
    oldest = {1: "old", 2: "gone"}
    newest = {2: "new", 3: None}
    answers = merge_answers([oldest, newest])
    assert answers[1] == "old"
    assert answers[2] == "new"
    assert answers[3] is None


def test_merge_answers_lets_a_tombstone_bury_the_value() -> None:
    answers = merge_answers([{5: "value"}, {5: None}])
    assert answers[5] is None
