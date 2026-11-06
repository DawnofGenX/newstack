"""Where patterns and texts come from, and the generators the stories trust."""

from __future__ import annotations

import pytest

from {{ package_name }}.corpus import (
    CorpusError,
    as_patterns,
    load_patterns,
    load_text,
    prose,
    random_text,
)


def test_a_lone_string_is_one_pattern(tmp_path) -> None:
    assert as_patterns("she") == ["she"]
    assert as_patterns(["he", "she"]) == ["he", "she"]


def test_patterns_of_the_wrong_shape_are_refused() -> None:
    with pytest.raises(CorpusError):
        as_patterns(7)


def test_a_pattern_list_skips_blanks_and_comments(tmp_path) -> None:
    path = tmp_path / "patterns.txt"
    path.write_text("# comment\nhe\n\nshe\n", encoding="utf-8")
    assert load_patterns(str(path)) == ["he", "she"]


def test_a_pattern_list_of_nothing_hunts_nothing(tmp_path) -> None:
    path = tmp_path / "empty.txt"
    path.write_text("# only a comment\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_patterns(str(path))


def test_a_missing_pattern_list_is_named(tmp_path) -> None:
    with pytest.raises(CorpusError):
        load_patterns(str(tmp_path / "gone.txt"))


def test_a_directory_is_not_a_pattern_list(tmp_path) -> None:
    with pytest.raises(CorpusError):
        load_patterns(str(tmp_path))


def test_a_text_is_read_verbatim_including_its_emptiness(tmp_path) -> None:
    path = tmp_path / "text.txt"
    path.write_text("a\nb\n", encoding="utf-8")
    assert load_text(str(path)) == "a\nb\n"
    path.write_text("", encoding="utf-8")
    assert load_text(str(path)) == ""


def test_a_missing_text_is_named(tmp_path) -> None:
    with pytest.raises(CorpusError):
        load_text(str(tmp_path / "gone.txt"))


def test_the_generator_is_deterministic_per_seed() -> None:
    assert random_text(40, seed=7) == random_text(40, seed=7)
    assert random_text(40, seed=7) != random_text(40, seed=8)


def test_the_generator_honours_its_alphabet() -> None:
    assert set(random_text(60, seed=3, alphabet="ab")) <= {"a", "b"}


def test_the_generator_refuses_impossible_spans() -> None:
    with pytest.raises(CorpusError):
        random_text(4, alphabet="")
    with pytest.raises(CorpusError):
        random_text(-1)


def test_the_prose_is_deterministic_and_worded() -> None:
    assert prose() == prose()
    assert prose(seed=1) != prose()
    assert len(prose().split()) == 160
