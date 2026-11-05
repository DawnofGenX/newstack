"""The core claims: the output is rebuilt, escaped, balanced, and stable."""

from __future__ import annotations

import pytest

from {{ package_name }} import demo as demo_mod
from {{ package_name }} import policy as policy_mod
from {{ package_name }} import sanitize as subject


@pytest.mark.parametrize(
    ("name", "source", "expected"),
    [
        (
            "a script block",
            "<p>hello</p><script>alert(1)</script><p>bye</p>",
            "<p>hello</p><p>bye</p>",
        ),
        ("an image with an event handler", '<img src=x onerror="alert(1)">', ""),
        ("a javascript url", '<a href="javascript:alert(1)">click</a>', "<a>click</a>"),
        (
            "a url that hides its scheme",
            '<a href="jav&#x09;ascript&#58;alert(1)">x</a>',
            "<a>x</a>",
        ),
        (
            "attributes nobody allowed",
            '<p onclick="steal()" style="color:red">text</p>',
            "<p>text</p>",
        ),
        ("markup that does not nest", "<b><i>bold italic</b></i>", "<b><i>bold italic</i></b>"),
        ("text that looks like markup", "5 < 6 & 7 > 2", "5 &lt; 6 &amp; 7 &gt; 2"),
        ("a comment", "<p>visible</p><!-- secret -->", "<p>visible</p>"),
    ],
)
def test_each_vector_has_one_expected_output(name: str, source: str, expected: str) -> None:
    assert subject.sanitize(source) == expected, name


@pytest.mark.parametrize(("name", "source", "_note"), demo_mod.VECTORS)
def test_the_output_is_a_fixed_point(name: str, source: str, _note: str) -> None:
    once = subject.sanitize(source)
    assert subject.sanitize(once) == once, name


@pytest.mark.parametrize(
    ("text", "want"),
    [
        ("javascript:alert(1)", "javascript"),
        ("JAVASCRIPT:alert(1)", "javascript"),
        ("jav\tascript:alert(1)", "javascript"),
        ("java\nscript:alert(1)", "javascript"),
        (" java\x00script:alert(1)", "javascript"),
        ("/docs/page", None),
        ("#top", None),
        ("a/b:c", None),
        ("HTTP://example.com", "http"),
        ("mailto:a@b", "mailto"),
    ],
)
def test_scheme_detection_ignores_what_browsers_ignore(text: str, want: str | None) -> None:
    assert subject.scheme_of(text) == want


@pytest.mark.parametrize(
    ("url", "allowed"),
    [
        ("https://example.com/a?b=1", True),
        ("http://example.com", True),
        ("mailto:a@b", True),
        ("tel:+100", True),
        ("/relative/path", True),
        ("javascript:alert(1)", False),
        ("data:text/html,<b>x</b>", False),
        ("vbscript:msgbox(1)", False),
        ("file:///etc/passwd", False),
    ],
)
def test_only_named_schemes_survive(url: str, allowed: bool) -> None:
    assert subject.url_is_allowed(url) is allowed


def test_attributes_are_emitted_in_one_order() -> None:
    assert subject.sanitize('<a title="y" href="/x">z</a>') == '<a href="/x" title="y">z</a>'


def test_a_quote_in_a_value_is_escaped() -> None:
    assert subject.sanitize('<a title="a&quot;b">x</a>') == '<a title="a&quot;b">x</a>'


def test_an_unclosed_element_is_closed() -> None:
    assert subject.sanitize("<b>x") == "<b>x</b>"


def test_nested_elements_close_inside_out() -> None:
    assert subject.sanitize("<b><i>x") == "<b><i>x</i></b>"


def test_a_void_element_is_not_closed() -> None:
    assert subject.sanitize("a<br>b") == "a<br>b"


def test_a_self_closed_element_is_written_out() -> None:
    assert subject.sanitize('<a href="/x" />') == '<a href="/x"></a>'


def test_a_stray_close_tag_is_dropped() -> None:
    assert subject.sanitize("x</b>") == "x"


def test_a_doctype_is_not_content() -> None:
    assert subject.sanitize("<!doctype html><p>x</p>") == "<p>x</p>"


def test_an_attribute_without_a_value_is_dropped() -> None:
    assert subject.sanitize("<p hidden>t</p>") == "<p>t</p>"


def test_the_counters_say_what_was_removed() -> None:
    output, stats = subject.explain('<img src=x onclick="a"><b>t</b>')
    assert output == "<b>t</b>"
    assert stats.tags_dropped == 1
    assert stats.content_dropped == 0


def test_a_script_block_is_counted_as_content_not_a_tag() -> None:
    output, stats = subject.explain("<script>x</script>")
    assert output == ""
    assert stats.content_dropped == 1
    assert stats.characters_dropped == 1


def test_a_refused_url_is_counted() -> None:
    _output, stats = subject.explain('<a href="javascript:1">x</a>')
    assert stats.urls_refused == 1


def test_comments_are_dropped_by_default() -> None:
    _output, stats = subject.explain("<!-- secret -->")
    assert stats.comments_dropped == 1


def test_a_policy_can_keep_comments_without_keeping_their_hazard() -> None:
    keep = policy_mod.Policy(allow_comments=True)
    kept = subject.sanitize("<!-- -- note -->", keep)
    assert kept.startswith("<!--") and kept.endswith("-->")
    assert "--" not in kept.removeprefix("<!--").removesuffix("-->")


def test_plain_text_is_escaped_not_removed() -> None:
    assert subject.sanitize("a < b & c") == "a &lt; b &amp; c"


def test_a_known_entity_in_text_survives_as_one_entity() -> None:
    assert subject.sanitize("a &amp; b") == "a &amp; b"


def test_an_unknown_entity_is_escaped_so_it_cannot_become_markup() -> None:
    assert subject.sanitize("a &lt;script&gt; b") == "a &lt;script&gt; b"


def test_a_non_string_is_refused() -> None:
    with pytest.raises(subject.SanitizeError, match="expected text"):
        subject.sanitize(42)  # type: ignore[arg-type]
