import pytest

from {{ package_name }} import truncate, word_count


def test_version_is_exposed() -> None:
    import {{ package_name }}

    assert {{ package_name }}.__version__ == "0.1.0"


@pytest.mark.parametrize(
    ("text", "expected"),
    [("", 0), ("hello", 1), ("hello world", 2), ("it's a test, isn't it?", 5)],
)
def test_word_count(text: str, expected: int) -> None:
    assert word_count(text) == expected


def test_truncate_leaves_short_text_alone() -> None:
    assert truncate("hello", 10) == "hello"


def test_truncate_cuts_long_text() -> None:
    assert truncate("hello world", 8) == "hello w…"
    assert len(truncate("x" * 100, 20)) == 20


def test_truncate_rejects_negative_limit() -> None:
    with pytest.raises(ValueError):
        truncate("abc", -1)
