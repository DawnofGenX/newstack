"""The audit judges the output, which is the only thing a browser will see."""

from __future__ import annotations

import pytest

from {{ package_name }} import audit as subject
from {{ package_name }} import demo as demo_mod


def test_a_clean_output_passes() -> None:
    verdict = subject.audit("<b>x</b>")
    assert verdict.ok
    assert verdict.output == "<b>x</b>"
    assert verdict.problems == ()


@pytest.mark.parametrize(("name", "source", "_note"), demo_mod.VECTORS)
def test_every_vector_passes_the_audit(name: str, source: str, _note: str) -> None:
    assert subject.audit(source).ok, name


@pytest.mark.parametrize(
    ("output", "want"),
    [
        ("<script>alert(1)</script>", 1),
        ('<p onclick="x">y</p>', 1),
        ("<iframe src=x></iframe>", 1),
        ('<a href="javascript:alert(1)">x</a>', 1),
        ('<a href="data:text/html;base64,xx">x</a>', 1),
        ("<p>javascript:alert(1)</p>", 0),
        ("<p>onclick= is a word here</p>", 0),
    ],
)
def test_the_scanner_reads_tags_not_prose(output: str, want: int) -> None:
    assert len(subject.problems(output)) == want


def test_a_second_pass_that_changes_the_output_is_not_ok() -> None:
    verdict = subject.audit("<b>x</b>")
    assert verdict.idempotent


def test_the_verdict_reports_the_counters() -> None:
    verdict = subject.audit("<script>x</script><b>y</b>")
    assert verdict.stats.content_dropped == 1
    assert verdict.output == "<b>y</b>"


def test_the_verdict_line_says_ok() -> None:
    assert subject.audit("<b>x</b>").line().startswith("ok")


def test_the_payload_is_json_ready() -> None:
    payload = subject.audit("<b>x</b>").as_dict()
    assert payload["ok"] is True
    assert payload["output"] == "<b>x</b>"
    assert payload["problems"] == []
    assert set(payload["stats"]) == {
        "tags_dropped",
        "attributes_dropped",
        "urls_refused",
        "content_dropped",
        "comments_dropped",
        "characters_dropped",
    }
