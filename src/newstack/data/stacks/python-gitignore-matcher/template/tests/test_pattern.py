"""Reading rules: what a line means before anything is matched."""

from __future__ import annotations

import pytest

from {{ package_name }} import pattern as subject


def test_a_comment_and_a_blank_line_are_not_rules() -> None:
    assert subject.parse_rule("# a comment", 1) is None
    assert subject.parse_rule("", 2) is None
    assert subject.parse_rule("   ", 3) is None


def test_a_bang_negates_and_the_prefix_leaves_the_body() -> None:
    rule = subject.parse_rule("!keep.log", 4)
    assert rule is not None
    assert rule.negated
    assert rule.text == "!keep.log"
    assert rule.body == "keep.log"
    assert rule.line == 4


def test_an_escaped_bang_is_a_name() -> None:
    rule = subject.parse_rule("\\!important", 5)
    assert rule is not None
    assert not rule.negated
    assert rule.body == "!important"
    assert rule.matches("!important", is_dir=False)


def test_an_escaped_hash_is_a_name() -> None:
    rule = subject.parse_rule("\\#notes", 6)
    assert rule is not None
    assert rule.body == "#notes"


def test_a_trailing_slash_marks_a_directory() -> None:
    rule = subject.parse_rule("build/", 7)
    assert rule is not None
    assert rule.dir_only
    assert rule.body == "build"
    assert not rule.matches("build", is_dir=False)
    assert rule.matches("build", is_dir=True)


def test_a_slash_anchors_and_a_bare_name_does_not() -> None:
    assert subject.parse_rule("/build", 1).anchored  # type: ignore[union-attr]
    assert not subject.parse_rule("build", 2).anchored  # type: ignore[union-attr]
    assert subject.parse_rule("logs/*.log", 3).anchored  # type: ignore[union-attr]


def test_trailing_spaces_are_dropped_unless_a_backslash_protects_them() -> None:
    assert subject.parse_rule("notes.txt   ", 1).body == "notes.txt"  # type: ignore[union-attr]
    protected = subject.parse_rule("notes.txt\\ ", 2)
    assert protected is not None
    assert protected.matches("notes.txt ", is_dir=False)


@pytest.mark.parametrize("line", ["!", "/", "file[0-9"])
def test_a_rule_that_names_nothing_is_refused(line: str) -> None:
    with pytest.raises(subject.PatternError):
        subject.parse_rule(line, 9)


def test_an_empty_rule_set_is_refused() -> None:
    with pytest.raises(subject.PatternError):
        subject.parse_rules(["# only a comment", ""])


def test_rule_numbers_survive_skipped_lines() -> None:
    rules = subject.parse_rules(["# a", "*.log", "", "!a.log"])
    assert [rule.line for rule in rules] == [2, 4]
