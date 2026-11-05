import pytest

from {{ package_name }} import Counts, count_text


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", Counts(lines=0, words=0, bytes=0)),
        ("hello world\n", Counts(lines=1, words=2, bytes=12)),
        ("\n\nx\n", Counts(lines=3, words=1, bytes=4)),
        ("abc", Counts(lines=0, words=1, bytes=3)),
        ("  \t ", Counts(lines=0, words=0, bytes=4)),
        # 12 characters, 14 bytes: the case a len(text) implementation gets wrong.
        ("héllo wörld\n", Counts(lines=1, words=2, bytes=14)),
        ("🙂\n", Counts(lines=1, words=1, bytes=5)),
    ],
)
def test_count_text_matches_wc(text: str, expected: Counts) -> None:
    assert count_text(text) == expected


def test_counts_are_immutable() -> None:
    counts = count_text("a\n")
    with pytest.raises(AttributeError):
        counts.words = 5  # type: ignore[misc]


def test_non_strings_are_rejected() -> None:
    with pytest.raises(TypeError, match="got int"):
        count_text(42)  # type: ignore[arg-type]
