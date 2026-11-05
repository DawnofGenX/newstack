"""The extension against the reference implementation, not against fixtures."""

from __future__ import annotations

import random

import pytest

from {{ package_name }} import (
    _speedups,
    count_bytes,
    count_str,
    reference,
    separators,
)


def test_the_counted_bytes_are_utf8_not_characters() -> None:
    text = "h\u00e9llo w\u00f6rld\n"
    assert len(text) == 12
    assert count_str(text) == (1, 2, 14)


def test_a_carriage_return_does_not_end_a_line() -> None:
    assert count_bytes(b"a b\r\nc\n") == (2, 3, 7)


def test_vertical_tab_and_form_feed_break_words() -> None:
    assert count_bytes(b"a\x0bb\x0cc") == (0, 3, 5)


def test_an_embedded_nul_is_an_ordinary_byte() -> None:
    # "s#" would stop at the NUL and report (2, 2, 1); "y#" reports the length.
    assert count_bytes(b"a\x00b c\n\n") == (2, 2, 7)


@pytest.mark.parametrize("size", [0, 1, 2, 7, 64, 512])
def test_it_agrees_with_the_reference_on_every_separator_sequence(size: int) -> None:
    alphabet = [0x20, 0x09, 0x0A, 0x0D, 0x0B, 0x0C, 0x00, 0x61, 0xC3, 0xA9]
    clock = random.Random(size)
    for _ in range(40):
        data = bytes(clock.choice(alphabet) for _ in range(size))
        assert count_bytes(data) == reference.count_bytes(data)


def test_it_agrees_with_the_reference_on_random_bytes() -> None:
    clock = random.Random(20261105)
    for _ in range(200):
        data = bytes(clock.randrange(256) for _ in range(clock.randrange(0, 120)))
        assert count_bytes(data) == reference.count_bytes(data)


def test_a_large_input_is_still_exact() -> None:
    data = (b"alpha beta\ngamma " * 20000) + b"\n"
    lines, words, size = count_bytes(data)
    assert (lines, words, size) == reference.count_bytes(data)
    assert size == len(data) == 340001


def test_it_accepts_bytearray_and_memoryview() -> None:
    for value in (bytearray(b"a b\n"), memoryview(b"a b\n")):
        assert count_bytes(value) == (1, 2, 4)


@pytest.mark.parametrize("value", ["text", 42, ["a"], None])
def test_it_refuses_anything_that_is_not_bytes(value: object) -> None:
    with pytest.raises(TypeError):
        count_bytes(value)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [b"text", 42, ["a"], None])
def test_count_str_refuses_anything_that_is_not_text(value: object) -> None:
    with pytest.raises(TypeError):
        count_str(value)  # type: ignore[arg-type]


def test_a_lone_surrogate_is_an_encoding_error_not_a_crash() -> None:
    with pytest.raises(UnicodeEncodeError):
        count_str("\ud800")


def test_the_separator_list_is_the_one_the_counters_use() -> None:
    assert separators() == b" \t\n\r\x0b\x0c"
    for byte in separators():
        assert count_bytes(b"a" + bytes([byte]) + b"b")[1] == 2


def test_the_extension_is_a_shared_object_and_not_python() -> None:
    assert _speedups.__file__.endswith((".so", ".pyd")), _speedups.__file__
    assert _speedups.__doc__


def test_the_cli_prints_json(tmp_path, capsys) -> None:
    from {{ package_name }} import cli

    sample = tmp_path / "sample.txt"
    sample.write_bytes(b"a b\n")
    assert cli.main([str(sample)]) == 0
    assert capsys.readouterr().out.strip() == '{"lines": 1, "words": 2, "bytes": 4}'


def test_the_cli_reports_a_missing_file_without_a_traceback(tmp_path, capsys) -> None:
    from {{ package_name }} import cli

    assert cli.main([str(tmp_path / "absent.txt")]) == 2
    assert "{{ npm_name }}:" in capsys.readouterr().err
