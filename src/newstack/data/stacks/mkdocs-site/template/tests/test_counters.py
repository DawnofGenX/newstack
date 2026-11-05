"""The counting rules the site documents."""

import pytest

from {{ package_name }} import Counts, count_text


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", Counts(lines=0, words=0, bytes=0)),
        ("hello world\n", Counts(lines=1, words=2, bytes=12)),
        ("a b\nc\n", Counts(lines=2, words=3, bytes=6)),
        ("\n\nx\n", Counts(lines=3, words=1, bytes=4)),
        ("  \t ", Counts(lines=0, words=0, bytes=4)),
        ("  padded  \n", Counts(lines=1, words=1, bytes=11)),
        ("héllo wörld\n", Counts(lines=1, words=2, bytes=14)),
        ("🙂\n", Counts(lines=1, words=1, bytes=5)),
    ],
)
def test_counts_match_wc(text: str, expected: Counts) -> None:
    assert count_text(text) == expected


def test_counts_are_immutable() -> None:
    counts = count_text("x\n")
    with pytest.raises(AttributeError):
        counts.lines = 2  # type: ignore[misc]


def test_a_non_string_raises() -> None:
    with pytest.raises(TypeError, match="count_text expects a string, got int"):
        count_text(42)  # type: ignore[arg-type]
