from __future__ import annotations

import pytest

from {{ package_name }} import apply as subject
from {{ package_name }} import diff as differ
from {{ package_name }} import model

BASE = "".join(f"line {n}\n" for n in range(1, 11))


def patch_of(old: str, new: str) -> model.FilePatch:
    return differ.diff_text(old, new)


def test_the_obvious_case_applies() -> None:
    new = BASE.replace("line 4\n", "line four\n")
    assert subject.apply_text(BASE, patch_of(BASE, new)).text == new


def test_a_patch_with_no_hunks_changes_nothing() -> None:
    applied = subject.apply_text(BASE, patch_of(BASE, BASE))
    assert applied.text == BASE
    assert applied.fuzz == ()


def test_an_insertion_at_the_top_lands_first() -> None:
    assert subject.apply_text(BASE, patch_of(BASE, "new\n" + BASE)).text == "new\n" + BASE


def test_deleting_the_first_line_works() -> None:
    new = BASE.replace("line 1\n", "")
    assert subject.apply_text(BASE, patch_of(BASE, new)).text == new


def test_a_missing_final_newline_survives_the_trip() -> None:
    assert subject.apply_text("a\nb", patch_of("a\nb", "a\nc")).text == "a\nc"


def test_a_hunk_is_found_again_after_lines_moved() -> None:
    patch = differ.parse_patch("--- a\n+++ b\n@@ -3,2 +3,2 @@\n line 5\n-line 6\n+line six\n")
    applied = subject.apply_text(BASE, patch)
    assert "line six\n" in applied.text
    assert applied.text.splitlines()[5] == "line six"
    assert applied.fuzz == ()


def test_a_hunk_that_matches_twice_is_refused() -> None:
    patch = differ.parse_patch("--- a\n+++ b\n@@ -5 +5 @@\n-same\n+other\n")
    with pytest.raises(model.ApplyError) as caught:
        subject.apply_text("same\nsame\n", patch)
    assert "matches at lines 1 and 2" in str(caught.value)


def test_a_mismatch_names_the_line_and_both_texts() -> None:
    patch = differ.parse_patch("--- a\n+++ b\n@@ -1,2 +1,2 @@\n line 1\n-line 2\n+line two\n")
    with pytest.raises(model.ApplyError) as caught:
        subject.apply_text(BASE.replace("line 1\n", "start\n"), patch)
    assert "line 1 is 'start'" in str(caught.value)
    assert "the patch expects 'line 1'" in str(caught.value)


def test_a_patch_beyond_the_end_of_the_file_is_refused() -> None:
    patch = differ.parse_patch("--- a\n+++ b\n@@ -40,2 +40,2 @@\n gone\n-also gone\n+new\n")
    with pytest.raises(model.ApplyError) as caught:
        subject.apply_text(BASE, patch)
    assert "the text ends after 10" in str(caught.value)


def test_an_empty_file_says_so() -> None:
    patch = differ.parse_patch("--- a\n+++ b\n@@ -1 +1 @@\n-a\n+b\n")
    with pytest.raises(model.ApplyError) as caught:
        subject.apply_text("", patch)
    assert "the file is empty" in str(caught.value)


def test_fuzz_applies_but_reports_what_it_tolerated() -> None:
    patch = differ.parse_patch(
        "--- a\n+++ b\n@@ -1,3 +1,3 @@\n line 1\n-line 2\n+line two\n line 3\n"
    )
    edited = BASE.replace("line 3\n", "line three\n")
    with pytest.raises(model.ApplyError):
        subject.apply_text(edited, patch)
    applied = subject.apply_text(edited, patch, fuzz=1)
    assert applied.fuzzy
    assert applied.fuzz == ((1, 1),)
    assert applied.text.splitlines()[2] == "line three"
    assert applied.line() == "applied   with fuzz: hunk 1 dropped 1"


def test_fuzz_zero_never_tolerates_anything() -> None:
    patch = differ.parse_patch(
        "--- a\n+++ b\n@@ -1,3 +1,3 @@\n line 1\n-line 2\n+line two\n line 3\n"
    )
    edited = BASE.replace("line 3\n", "line three\n")
    with pytest.raises(model.ApplyError):
        subject.apply_text(edited, patch, fuzz=0)


def test_a_negative_fuzz_is_refused() -> None:
    with pytest.raises(model.ApplyError):
        subject.apply_text(BASE, patch_of(BASE, BASE), fuzz=-1)


def test_hunks_out_of_order_are_refused() -> None:
    late = differ.parse_patch("--- a\n+++ b\n@@ -8 +8 @@\n-line 8\n+eight\n")
    early = differ.parse_patch("--- a\n+++ b\n@@ -2 +2 @@\n-line 2\n+two\n")
    patch = model.FilePatch("a", "b", (late.hunks[0], early.hunks[0]))
    with pytest.raises(model.ApplyError) as caught:
        subject.apply_text(BASE, patch)
    assert "out of order" in str(caught.value)


def test_applying_twice_is_refused() -> None:
    patch = patch_of(BASE, BASE.replace("line 7\n", "seven\n"))
    once = subject.apply_text(BASE, patch).text
    with pytest.raises(model.ApplyError):
        subject.apply_text(once, patch)


def test_every_kind_of_edit_round_trips() -> None:
    for label, new in (
        ("insert", BASE.replace("line 5\n", "line 5\nline 5b\n")),
        ("delete", BASE.replace("line 5\n", "")),
        ("rewrite all", "".join(f"row {n}\n" for n in range(1, 31))),
        ("to empty", ""),
    ):
        applied = subject.apply_text(BASE, patch_of(BASE, new))
        assert applied.text == new, label
