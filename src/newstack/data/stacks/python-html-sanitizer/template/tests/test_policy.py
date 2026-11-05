"""The allowlist is data, so it can be checked without sanitizing anything."""

from __future__ import annotations

import pytest

from {{ package_name }} import policy as subject


def test_the_default_policy_is_an_allowlist() -> None:
    assert "p" in subject.DEFAULT.allowed_tags
    assert "script" not in subject.DEFAULT.allowed_tags
    assert "iframe" not in subject.DEFAULT.allowed_tags


def test_attributes_are_per_tag() -> None:
    assert subject.DEFAULT.attributes_for("a") == frozenset({"href", "title"})
    assert subject.DEFAULT.attributes_for("p") == frozenset()


def test_an_unknown_tag_has_no_attributes() -> None:
    assert subject.DEFAULT.attributes_for("marquee") == frozenset()


def test_attributes_on_a_tag_the_policy_forbids_is_a_contradiction() -> None:
    with pytest.raises(subject.PolicyError, match="not an allowed tag"):
        subject.Policy(frozenset({"p"}), {"a": frozenset({"href"})})


def test_allowing_a_content_dropping_tag_is_a_contradiction() -> None:
    with pytest.raises(subject.PolicyError, match="drops its content"):
        subject.Policy(frozenset({"script"}))


@pytest.mark.parametrize("scheme", ["java script", "ht!tp", ""])
def test_a_scheme_must_be_a_name(scheme: str) -> None:
    with pytest.raises(subject.PolicyError, match="not a scheme"):
        subject.Policy(allowed_schemes=frozenset({scheme}))


def test_a_custom_policy_can_widen_the_allowlist() -> None:
    widened = subject.Policy(subject.DEFAULT.allowed_tags | {"img"}, {"img": frozenset({"alt"})})
    assert widened.attributes_for("img") == frozenset({"alt"})
    assert "img" in widened.allowed_tags


def test_the_default_policy_allows_no_inline_style() -> None:
    assert "style" not in subject.DEFAULT.allowed_tags
    assert "class" not in subject.DEFAULT.attributes_for("p")
