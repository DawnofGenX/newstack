from __future__ import annotations

import pytest

from {{ package_name }} import merge as subject

BASE = "a\nb\nc\nd\n"


def test_an_untouched_file_is_the_file() -> None:
    result = subject.merge_text(BASE, BASE, BASE)
    assert result.text == BASE
    assert result.conflicts == 0
    assert [chunk.kind for chunk in result.chunks] == ["same"]


def test_edits_in_different_places_both_land() -> None:
    result = subject.merge_text(BASE, "a\nB\nc\nd\n", "a\nb\nc\nD\n")
    assert result.text == "a\nB\nc\nD\n"
    assert result.conflicts == 0
    assert [chunk.kind for chunk in result.chunks] == ["same", "ours", "same", "theirs"]


def test_the_same_edit_twice_is_agreed_not_conflicted() -> None:
    edited = "a\nb\nC\nd\n"
    result = subject.merge_text(BASE, edited, edited)
    assert result.conflicts == 0
    assert result.agreed == 1
    assert result.text == edited


def test_two_insertions_at_the_same_point_conflict() -> None:
    result = subject.merge_text(BASE, "a\nx\nb\nc\nd\n", "a\ny\nb\nc\nd\n")
    assert result.conflicts == 1
    assert "<<<<<<< ours\nx\n=======\ny\n>>>>>>> theirs\n" in result.text


def test_an_insertion_at_a_boundary_does_not_conflict_with_a_replacement_there() -> None:
    result = subject.merge_text(BASE, "a\nx\nb\nc\nd\n", "a\nB\nc\nd\n")
    assert result.conflicts == 0
    assert result.text == "a\nx\nB\nc\nd\n"


def test_overlapping_replacements_conflict_and_keep_both_sides() -> None:
    result = subject.merge_text(BASE, "a\nXX\nc\nd\n", "a\nYY\nc\nd\n")
    assert result.conflicts == 1
    assert "XX" in result.text and "YY" in result.text


def test_a_conflict_is_widened_to_the_overlapping_region() -> None:
    ours = "a\nB\nc\nd\n"
    theirs = "a\nb\nC\nd\n"
    result = subject.merge_text(BASE, ours, theirs)
    # b and c are adjacent base lines; replacing one and the other is clean.
    assert result.conflicts == 0
    assert result.text == "a\nB\nC\nd\n"


def test_two_sides_deleting_different_lines_both_delete() -> None:
    result = subject.merge_text(BASE, "a\nb\nc\n", "b\nc\nd\n")
    assert result.conflicts == 0
    assert result.text == "b\nc\n"


def test_labels_are_written_into_the_markers() -> None:
    result = subject.merge_text(BASE, "a\nB\nc\nd\n", "a\nZ\nc\nd\n", labels=("feature", "main"))
    assert "<<<<<<< feature\n" in result.text
    assert ">>>>>>> main\n" in result.text


def test_diff3_style_keeps_the_base_section() -> None:
    result = subject.merge_text(BASE, "a\nB\nc\nd\n", "a\nZ\nc\nd\n", style=subject.DIFF3)
    assert "||||||| base\nb\n" in result.text
    plain = subject.merge_text(BASE, "a\nB\nc\nd\n", "a\nZ\nc\nd\n")
    assert "|||||||" not in plain.text


def test_an_unknown_style_is_refused() -> None:
    with pytest.raises(subject.MergeError, match="is not a marker style"):
        subject.merge_text(BASE, BASE, BASE, style="squash")


def test_an_empty_label_is_refused() -> None:
    with pytest.raises(subject.MergeError, match="cannot be empty"):
        subject.merge_text(BASE, BASE, BASE, labels=("ours", " "))


def test_a_label_with_a_newline_is_refused() -> None:
    with pytest.raises(subject.MergeError, match="cannot contain a newline"):
        subject.merge_text(BASE, BASE, BASE, labels=("ou\nrs", "theirs"))


def test_a_span_without_a_final_newline_still_gets_its_marker_on_a_line() -> None:
    result = subject.merge_text("a\nb", "a\nB", "a\nZ")
    assert result.text == "a\n<<<<<<< ours\nB\n=======\nZ\n>>>>>>> theirs\n"


def test_an_empty_base_can_take_one_sides_text() -> None:
    result = subject.merge_text("", "", "new\n")
    assert result.text == "new\n"
    assert result.conflicts == 0


def test_an_empty_base_with_two_different_texts_conflicts() -> None:
    result = subject.merge_text("", "ours\n", "theirs\n")
    assert result.conflicts == 1


def test_unchanged_ours_means_the_result_is_theirs_exactly() -> None:
    theirs = "a\nB\nc\nD\n"
    assert subject.merge_text(BASE, BASE, theirs).text == theirs


def test_unchanged_theirs_means_the_result_is_ours_exactly() -> None:
    ours = "A\nb\nC\nd\n"
    assert subject.merge_text(BASE, ours, BASE).text == ours


def test_swapping_the_sides_keeps_the_conflict_count() -> None:
    ours, theirs = "a\nB\nc\nd\n", "a\nZ\nc\nd\n"
    assert (
        subject.merge_text(BASE, ours, theirs).conflicts
        == subject.merge_text(BASE, theirs, ours).conflicts
    )


def test_the_summary_counts_both_sides_and_the_conflicts() -> None:
    result = subject.merge_text(BASE, "a\nB\nc\nd\n", "a\nZ\nc\nD\n")
    assert result.summary().startswith("chunks ")
    assert "1 change(s) from ours" in result.summary()
    assert "1 conflict(s)" in result.summary()


def test_the_chunk_lines_name_each_region() -> None:
    result = subject.merge_text(BASE, "a\nB\nc\nd\n", "a\nb\nc\nD\n")
    lines = result.lines()
    assert len(lines) == len(result.chunks)
    assert lines[1].startswith(" 2  ours")


def test_merge_files_reads_three_paths(tmp_path) -> None:
    for name, text in (("base", BASE), ("ours", "a\nB\nc\nd\n"), ("theirs", BASE)):
        (tmp_path / f"{name}.txt").write_text(text, encoding="utf-8")
    result = subject.merge_files(
        tmp_path / "base.txt", tmp_path / "ours.txt", tmp_path / "theirs.txt"
    )
    assert result.text == "a\nB\nc\nd\n"
