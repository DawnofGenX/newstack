from __future__ import annotations

import pytest

from {{ package_name }} import model as subject

BASE = "line 1\nline 2\nline 3\n"


def test_splitting_keeps_what_ending_each_line_has() -> None:
    assert subject.split_lines("a\nb\n") == ["a\n", "b\n"]
    assert subject.split_lines("a\nb") == ["a\n", "b"]
    assert subject.split_lines("") == []
    assert subject.split_lines("\n") == ["\n"]


def test_a_missing_newline_is_named_in_messages() -> None:
    assert subject.shown("a\n") == "'a'"
    assert "without a trailing newline" in subject.shown("a")


def test_a_header_leaves_out_a_count_of_one() -> None:
    hunk = subject.Hunk(3, 1, 3, 1, ((" ", "x\n"),))
    assert hunk.header() == "@@ -3 +3 @@"


def test_a_header_states_a_count_of_zero() -> None:
    hunk = subject.Hunk(0, 0, 1, 2, (("+", "x\n"), ("+", "y\n")))
    assert hunk.header() == "@@ -0,0 +1,2 @@"


def test_a_section_heading_is_kept_in_the_header() -> None:
    hunk = subject.Hunk(1, 1, 1, 1, ((" ", "x\n"),), section="def f():")
    assert hunk.header() == "@@ -1 +1 @@ def f():"


def test_the_sides_of_a_hunk_are_the_kinds_that_belong_to_them() -> None:
    hunk = subject.Hunk(1, 2, 1, 2, ((" ", "ctxt\n"), ("-", "gone\n"), ("+", "new\n")))
    assert hunk.old_lines == ["ctxt\n", "gone\n"]
    assert hunk.new_lines == ["ctxt\n", "new\n"]


def test_context_counts_stop_at_the_first_change() -> None:
    hunk = subject.Hunk(1, 5, 1, 5, (
        (" ", "a\n"), (" ", "b\n"), ("-", "c\n"), ("+", "d\n"), (" ", "e\n"),
    ))
    assert hunk.leading_context == 2
    assert hunk.trailing_context == 1


def test_a_patch_counts_its_own_additions() -> None:
    patch = subject.FilePatch("a", "b", (
        subject.Hunk(1, 1, 1, 2, (("-", "x\n"), ("+", "y\n"), ("+", "z\n"))),
    ))
    assert patch.added == 2
    assert patch.removed == 1
    assert patch.line() == "a -> b: 1 hunk(s), +2 -1"


def test_the_error_types_are_distinct() -> None:
    assert issubclass(subject.ParseError, subject.DiffError)
    assert issubclass(subject.ApplyError, subject.DiffError)
    with pytest.raises(subject.DiffError):
        raise subject.ApplyError("nope")
