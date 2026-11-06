from __future__ import annotations

import pytest

from {{ package_name }} import change as subject


def test_identical_texts_have_no_changes() -> None:
    assert subject.changes("a\nb\n", "a\nb\n") == []


def test_a_replaced_line_is_one_change() -> None:
    found = subject.changes("a\nb\nc\n", "a\nB\nc\n")
    assert len(found) == 1
    assert (found[0].start, found[0].end) == (1, 2)
    assert found[0].lines == ("B\n",)
    assert found[0].replaced == 1


def test_an_insertion_consumes_no_base_line() -> None:
    found = subject.changes("a\nc\n", "a\nb\nc\n")
    assert found[0].inserted
    assert not found[0].deleted
    assert (found[0].start, found[0].end) == (1, 1)


def test_a_deletion_contributes_no_lines() -> None:
    found = subject.changes("a\nb\n", "a\n")
    assert found[0].deleted
    assert found[0].lines == ()


def test_autojunk_is_off_so_repeated_lines_are_not_called_changes() -> None:
    base = "".join(f"line {index}\n" for index in range(80))
    other = base.replace("line 40\n", "line 40 changed\n")
    assert len(subject.changes(base, other)) == 1


def test_adjacent_replacements_do_not_touch() -> None:
    left = subject.Change(2, 3, ("x\n",))
    right = subject.Change(3, 4, ("y\n",))
    assert not left.touches(right)


def test_overlapping_replacements_touch() -> None:
    left = subject.Change(2, 5, ("x\n",))
    right = subject.Change(4, 6, ("y\n",))
    assert left.touches(right)
    assert right.touches(left)


def test_insertions_at_the_same_point_touch() -> None:
    left = subject.Change(3, 3, ("x\n",))
    right = subject.Change(3, 3, ("y\n",))
    assert left.touches(right)


def test_insertions_at_different_points_do_not_touch() -> None:
    assert not subject.Change(3, 3, ("x\n",)).touches(subject.Change(4, 4, ("y\n",)))


def test_an_insertion_does_not_touch_a_neighbouring_replacement() -> None:
    assert not subject.Change(3, 3, ("x\n",)).touches(subject.Change(3, 4, ("y\n",)))


def test_the_line_describes_what_the_change_does() -> None:
    assert subject.Change(2, 4, ("x\n",)).line(1) == " 1  replace base 2..4 with 1 line(s)"
    assert subject.Change(2, 4, ()).line(2) == " 2  delete base 2..4"
    assert subject.Change(2, 2, ("x\n", "y\n")).line(3) == " 3  insert 2 line(s) at 2"


def test_a_missing_final_newline_is_part_of_the_line() -> None:
    found = subject.changes("a\nb\n", "a\nb")
    assert found[0].start == 1
    assert found[0].lines == ("b",)
    assert subject.changes("a\nb", "a\nb") == []


def test_lists_are_accepted_as_well_as_text() -> None:
    assert subject.changes(["a\n"], ["a\n", "b\n"]) == [subject.Change(1, 1, ("b\n",))]


@pytest.mark.parametrize("other", ["", "a\n", "a\nb\nc\n"])
def test_changes_are_reversible_by_construction(other) -> None:
    base = "a\nb\n"
    found = subject.changes(base, other)
    rebuilt = list(subject.split_lines(base))
    for change in sorted(found, key=lambda item: item.start, reverse=True):
        rebuilt[change.start : change.end] = list(change.lines)
    assert "".join(rebuilt) == other
