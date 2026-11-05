from __future__ import annotations

import pytest

from {{ package_name }} import diff as subject
from {{ package_name }} import model

BASE = "".join(f"line {n}\n" for n in range(1, 11))


def test_identical_texts_have_no_hunks() -> None:
    assert subject.diff_text(BASE, BASE).hunks == ()


def test_one_changed_line_is_one_hunk_with_context() -> None:
    patch = subject.diff_text(BASE, BASE.replace("line 5\n", "line five\n"))
    assert len(patch.hunks) == 1
    hunk = patch.hunks[0]
    assert hunk.old_start == 2
    assert hunk.old_count == 7
    assert [kind for kind, _ in hunk.lines].count(" ") == 6


def test_context_zero_shows_only_the_change() -> None:
    patch = subject.diff_text(BASE, BASE.replace("line 5\n", "five\n"), 0)
    kinds = [kind for kind, _ in patch.hunks[0].lines]
    assert kinds == ["-", "+"]
    assert patch.hunks[0].old_start == 5


def test_two_distant_changes_are_two_hunks() -> None:
    edited = BASE.replace("line 2\n", "two\n").replace("line 10\n", "ten\n")
    assert len(subject.diff_text(BASE, edited).hunks) == 2


def test_two_nearby_changes_share_one_hunk() -> None:
    edited = BASE.replace("line 4\n", "four\n").replace("line 5\n", "five\n")
    assert len(subject.diff_text(BASE, edited).hunks) == 1


def test_an_insertion_at_the_top_names_line_zero() -> None:
    patch = subject.diff_text("", "first\n")
    assert patch.hunks[0].old_start == 0
    assert patch.hunks[0].old_count == 0
    assert patch.hunks[0].new_start == 1


def test_a_format_parse_round_trip_keeps_the_hunks() -> None:
    patch = subject.diff_text(BASE, BASE.replace("line 7\n", "seven\n"))
    again = subject.parse_patch(subject.format_patch(patch))
    assert again.hunks == patch.hunks
    assert again.old_path == patch.old_path


def test_a_section_heading_survives() -> None:
    text = "--- a\n+++ b\n@@ -1,1 +1,1 @@ def f():\n-x\n+y\n"
    assert subject.parse_patch(text).hunks[0].section == "def f():"


def test_a_missing_newline_is_marked_on_both_sides() -> None:
    text = subject.format_patch(subject.diff_text("a\nb", "a\nc"))
    assert text.count(model.NO_NEWLINE) == 2
    assert text.endswith(model.NO_NEWLINE + "\n")


def test_reading_the_marker_back_removes_the_newline() -> None:
    patch = subject.diff_text("a\nb", "a\nc")
    again = subject.parse_patch(subject.format_patch(patch))
    assert again.hunks[0].old_lines[-1] == "b"
    assert again.hunks[0].new_lines[-1] == "c"


def test_git_metadata_before_the_headers_is_ignored() -> None:
    text = "diff --git a/x b/x\nindex 111..222\n--- a\n+++ b\n@@ -1 +1 @@\n-a\n+b\n"
    assert subject.parse_patch(text).hunks[0].new_lines == ["b\n"]


@pytest.mark.parametrize(
    ("label", "text"),
    [
        ("no headers", "hello\n"),
        ("headers without hunks", "--- a\n+++ b\n"),
        ("a count that lies", "--- a\n+++ b\n@@ -1,3 +1 @@\n-a\n+b\n"),
        ("a body line", "--- a\n+++ b\n@@ -1 +1 @@\nx\n"),
        ("a second file", "--- a\n+++ b\n@@ -1 +1 @@\n-a\n+b\n--- c\n+++ d\n"),
        ("a range", "--- a\n+++ b\n@@ -x +1 @@\n-a\n+b\n"),
        ("a marker", "--- a\n+++ b\n@@ -1 +1 @@\n\\ No newline at end of file\n"),
    ],
)
def test_parse_refuses_what_it_cannot_read(label: str, text: str) -> None:
    with pytest.raises(model.ParseError):
        subject.parse_patch(text)


def test_a_negative_context_is_refused() -> None:
    with pytest.raises(model.ApplyError):
        subject.diff_lines(["a\n"], ["b\n"], -1)
