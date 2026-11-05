"""The file is the unit of trust, so the parser is tested before anything runs."""

from __future__ import annotations

import hashlib

import pytest

from {{ package_name }}.migration import Migration, MigrationError, load


def write(folder, name: str, sql: str = "SELECT 1;\n"):
    path = folder / name
    path.write_text(sql, encoding="utf-8")
    return path


def test_files_are_ordered_by_number_not_by_name(tmp_path) -> None:
    for name in ("10_ten.sql", "9_nine.sql", "2_two.sql"):
        write(tmp_path, name)
    assert [migration.migration_id for migration in load(tmp_path)] == ["2", "9", "10"]


def test_the_checksum_covers_the_bytes_on_disk(tmp_path) -> None:
    path = write(tmp_path, "0001_init.sql", "CREATE TABLE t (x);\n")
    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    assert load(tmp_path)[0].checksum == expected


def test_a_trailing_newline_changes_the_checksum(tmp_path) -> None:
    write(tmp_path, "0001_init.sql", "CREATE TABLE t (x);")
    before = load(tmp_path)[0].checksum
    write(tmp_path, "0001_init.sql", "CREATE TABLE t (x);\n")
    assert load(tmp_path)[0].checksum != before


def test_a_name_that_cannot_be_ordered_is_refused(tmp_path) -> None:
    write(tmp_path, "init.sql")
    with pytest.raises(MigrationError, match=r"expected <number>_<lower_snake_case>\.sql"):
        load(tmp_path)


def test_an_empty_file_is_refused(tmp_path) -> None:
    write(tmp_path, "0001_init.sql", "  \n\n")
    with pytest.raises(MigrationError, match="the file is empty"):
        load(tmp_path)


def test_two_files_cannot_claim_the_same_position(tmp_path) -> None:
    write(tmp_path, "0002_a.sql")
    write(tmp_path, "0002_b.sql")
    with pytest.raises(MigrationError, match="0002 is claimed twice") as caught:
        load(tmp_path)
    assert "0002_a.sql" in str(caught.value)
    assert "0002_b.sql" in str(caught.value)


def test_a_gap_in_the_numbering_is_allowed(tmp_path) -> None:
    write(tmp_path, "0001_a.sql")
    write(tmp_path, "0003_c.sql")
    assert [migration.slug for migration in load(tmp_path)] == ["a", "c"]


def test_a_missing_directory_is_reported_as_such(tmp_path) -> None:
    with pytest.raises(MigrationError, match="not a directory"):
        load(tmp_path / "nope")


def test_the_short_checksum_is_twelve_characters(tmp_path) -> None:
    write(tmp_path, "0001_init.sql")
    migration: Migration = load(tmp_path)[0]
    assert len(migration.short()) == 12
    assert migration.checksum.startswith(migration.short())
