"""The version: fields, precedence, and what it refuses."""

import pytest

from {{ package_name }} import version as subject


def test_fields_are_numbers_not_decimals():
    assert subject.parse("1.10.0") > subject.parse("1.9.0")
    assert subject.compare(subject.parse("1.10.0"), subject.parse("1.9.0")) == 1


def test_prereleases_sort_below_the_release():
    chain = ["1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-beta", "1.0.0-beta.11", "1.0.0"]
    parsed = [subject.parse(text) for text in chain]
    assert parsed == sorted(parsed)


def test_numeric_identifiers_are_compared_as_numbers():
    assert subject.parse("1.0.0-alpha.9") < subject.parse("1.0.0-alpha.10")


def test_a_numeric_identifier_sorts_below_an_alphanumeric_one():
    assert subject.parse("1.0.0-1") < subject.parse("1.0.0-alpha")


def test_build_metadata_does_not_take_part_in_precedence():
    assert subject.parse("1.0.0+left") == subject.parse("1.0.0+right")


def test_the_string_round_trips():
    text = "1.2.3-rc.1+build.7"
    assert str(subject.parse(text)) == text


@pytest.mark.parametrize("text", ["1.02.3", "1.2", "1.2.3-", "1.2.3-01", "v1.2.3", "1.2.3.4"])
def test_a_string_that_is_not_a_version_is_refused(text):
    with pytest.raises(subject.VersionError):
        subject.parse(text)


def test_the_refusal_says_why():
    with pytest.raises(subject.VersionError, match="leading zero"):
        subject.parse("1.02.3")
    with pytest.raises(subject.VersionError, match=r"major\.minor\.patch"):
        subject.parse("1.2")


def test_versions_hash_by_precedence():
    assert len({subject.parse("1.0.0+a"), subject.parse("1.0.0+b")}) == 1
