"""Canonical form: one spelling per request."""

from __future__ import annotations

import pytest

from {{ package_name }} import canonical as subject


def test_unreserved_characters_pass_through() -> None:
    assert subject.encode("aZ0-_.~") == "aZ0-_.~"


def test_a_space_becomes_percent_twenty_with_uppercase_hex() -> None:
    assert subject.encode("a b") == "a%20b"
    assert subject.encode("ç") == "%C3%A7"


def test_decode_does_not_treat_a_plus_as_a_space() -> None:
    assert subject.decode("a+b") == "a+b"
    assert subject.decode("a%2Bb") == "a+b"


def test_a_truncated_escape_is_refused() -> None:
    with pytest.raises(subject.CanonicalError, match="percent escape"):
        subject.decode("%4")


def test_a_host_cannot_be_signed() -> None:
    with pytest.raises(subject.CanonicalError, match="sign the path"):
        subject.request_line("GET", "https://example.test/a")


def test_a_fragment_is_refused() -> None:
    with pytest.raises(subject.CanonicalError, match="fragment"):
        subject.request_line("GET", "/a#top")


def test_a_relative_path_is_refused() -> None:
    with pytest.raises(subject.CanonicalError, match="absolute path"):
        subject.request_line("GET", "a/b")


def test_the_query_is_sorted_by_name_then_value() -> None:
    assert subject.request_line("GET", "/a?b=2&a=9&a=1")[1] == "/a?a=1&a=9&b=2"


def test_an_empty_query_leaves_no_question_mark() -> None:
    assert subject.request_line("GET", "/a?")[1] == "/a"
    assert subject.request_line("GET", "/a")[1] == "/a"


def test_two_spellings_reach_one_canonical_path() -> None:
    escaped = subject.request_line("GET", "/files/%7euser/report")[1]
    plain = subject.request_line("GET", "/files/~user/report")[1]
    assert escaped == plain == "/files/~user/report"


def test_the_method_keeps_its_case_insensitive_spelling() -> None:
    assert subject.request_line("delete", "/a")[0] == "DELETE"


def test_an_escaped_slash_stays_inside_its_segment() -> None:
    assert subject.request_line("GET", "/a%2Fb")[1] == "/a%2Fb"
    assert subject.request_line("GET", "/a/b")[1] == "/a/b"
