"""Request parsing is strict; result parsing is resumable."""

from __future__ import annotations

import pytest

from {{ package_name }}.records import (
    RecordError,
    Result,
    ResultWriter,
    load_results,
    parse_requests,
    parse_results,
)


def test_parses_requests_in_order_and_skips_blank_lines() -> None:
    rows = parse_requests(['{"id": "a", "prompt": "hi"}', "", '{"id": "b", "prompt": "yo"}'])
    assert [row.id for row in rows] == ["a", "b"]


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("[1, 2]", "expected a JSON object"),
        ("nope", "not JSON"),
        ('{"id": "a"}', "no string prompt"),
        ('{"prompt": "x"}', "non-empty string id"),
        ('{"id": "", "prompt": "x"}', "non-empty string id"),
    ],
)
def test_rejects_bad_request_lines_with_the_line_number(line: str, message: str) -> None:
    with pytest.raises(RecordError) as caught:
        parse_requests([line], "req.jsonl")
    assert "req.jsonl:1" in str(caught.value)
    assert message in str(caught.value)


def test_rejects_a_duplicate_id_and_names_the_first_line() -> None:
    with pytest.raises(RecordError, match="duplicate id 'a', first seen on line 1"):
        parse_requests(['{"id": "a", "prompt": "x"}', '{"id": "a", "prompt": "y"}'])


def test_rejects_an_empty_batch() -> None:
    with pytest.raises(RecordError, match="no requests"):
        parse_requests(["", "   "])


def test_result_round_trips_through_its_json_line() -> None:
    result = Result(id="a", output="héllo", model="m", tokens_in=2, tokens_out=3, attempts=1)
    assert Result.from_line(result.line()) == result
    assert "héllo" in result.line(), "non-ASCII text is kept as UTF-8, not escaped"


def test_a_torn_final_line_is_discarded_but_a_broken_middle_line_raises() -> None:
    done = parse_results(['{"id": "a", "output": "x"}', '{"id": "b", "outp'])
    assert list(done) == ["a"]
    with pytest.raises(RecordError, match=r"results\.jsonl:1"):
        parse_results(['{"id": "a", "outp', '{"id": "b", "output": "y"}'], "results.jsonl")


def test_failed_results_are_recorded_not_dropped(tmp_path) -> None:
    out = tmp_path / "results.jsonl"
    with ResultWriter(out) as writer:
        writer.write(Result(id="a", ok=False, error="http 400"))
    done = load_results(out)
    assert done["a"].ok is False
    assert done["a"].error == "http 400"


def test_loading_a_missing_results_file_is_not_an_error(tmp_path) -> None:
    assert load_results(tmp_path / "nothing.jsonl") == {}


def test_writer_appends_so_a_rerun_keeps_earlier_answers(tmp_path) -> None:
    out = tmp_path / "results.jsonl"
    with ResultWriter(out) as writer:
        writer.write(Result(id="a", output="one"))
    with ResultWriter(out) as writer:
        writer.write(Result(id="b", output="two"))
    assert sorted(load_results(out)) == ["a", "b"]
