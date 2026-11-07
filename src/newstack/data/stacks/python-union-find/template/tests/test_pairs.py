from __future__ import annotations

import pytest

from {{ package_name }}.pairs import (
    PairError,
    load_pairs,
    synthetic,
)


def write(path: object, text: str) -> str:
    location = str(path)
    with open(location, "w", encoding="utf-8") as handle:
        handle.write(text)
    return location


def test_a_workload_file_skips_blanks_and_comments(tmp_path: object) -> None:
    path = write(tmp_path / "pairs.txt", "# header\n\n1 2\n\n3 4\n")
    assert load_pairs(path) == [(1, 2), (3, 4)]


def test_a_missing_workload_is_named(tmp_path: object) -> None:
    with pytest.raises(PairError, match="no such workload"):
        load_pairs(f"{tmp_path}/gone.txt")


def test_a_directory_is_not_a_workload() -> None:
    with pytest.raises(PairError, match="directory"):
        load_pairs(".")


def test_a_lone_integer_is_not_a_pair(tmp_path: object) -> None:
    path = write(tmp_path / "odd.txt", "7\n")
    with pytest.raises(PairError, match="not a pair"):
        load_pairs(path)


def test_a_word_is_not_a_pair(tmp_path: object) -> None:
    path = write(tmp_path / "word.txt", "seven 3\n")
    with pytest.raises(PairError, match="not a pair"):
        load_pairs(path)


def test_a_comment_only_file_holds_no_workload(tmp_path: object) -> None:
    path = write(tmp_path / "empty.txt", "# nothing\n")
    with pytest.raises(PairError, match="no pairs"):
        load_pairs(path)


def test_the_generator_is_fixed_per_seed() -> None:
    first = synthetic(30, seed=11)
    assert first == synthetic(30, seed=11)
    assert first != synthetic(30, seed=12)


def test_the_generator_stays_in_its_span() -> None:
    for first, second in synthetic(50, seed=4, low=10, high=20):
        assert 10 <= first < 20
        assert 10 <= second < 20


def test_an_empty_request_is_refused() -> None:
    with pytest.raises(PairError):
        synthetic(0)
    with pytest.raises(PairError):
        synthetic(4, low=9, high=9)
