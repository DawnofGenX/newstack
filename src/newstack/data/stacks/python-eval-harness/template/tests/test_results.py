import json

import pytest

from {{ package_name }} import harness, results
from {{ package_name }}.dataset import Example

EXAMPLES = [Example(id="a", prompt="q", gold="Paris"), Example(id="b", prompt="q", gold="Tokyo")]


def record(predictions, run_id="run", **kwargs):
    report = harness.evaluate(EXAMPLES, predictions)
    return results.build(report, run_id=run_id, created="2026-01-01T00:00:00Z", **kwargs)


def test_a_record_carries_its_provenance():
    data = record({"a": "Paris", "b": "Tokyo"}, commit="abc123")
    assert data["run_id"] == "run"
    assert data["commit"] == "abc123"
    assert data["created"] == "2026-01-01T00:00:00Z"
    assert data["format"] == results.FORMAT
    assert data["score"] == 1.0


def test_a_record_round_trips_through_a_file(tmp_path):
    path = tmp_path / "run.json"
    results.write(path, record({"a": "Paris", "b": "Tokyo"}))
    assert results.read(path)["run_id"] == "run"
    assert json.loads(path.read_text())["score"] == 1.0


def test_compare_reports_an_aggregate_delta():
    diff = results.compare(record({"a": "Paris"}), record({"a": "Paris", "b": "Tokyo"}))
    assert diff.delta == pytest.approx(0.5)
    assert not diff.regressed


def test_a_missing_prediction_shows_up_as_a_regression_on_that_id():
    diff = results.compare(record({"a": "Paris", "b": "Tokyo"}), record({"a": "Paris"}))
    assert [key for key, _before, _after in diff.regressions] == ["b"]


def test_tolerance_absorbs_a_small_drop_but_not_an_equal_one():
    before = record({"a": "Paris", "b": "Tokyo"})
    after = record({"a": "Paris dy", "b": "Tokyo"})
    assert results.compare(before, after).regressed
    assert not results.compare(before, after, tolerance=0.5).regressed
    # a 1.0 -> 0.667 drop is 0.333, which survives a 0.2 tolerance
    assert results.compare(before, after, tolerance=0.2).regressed


def test_compare_lists_ids_that_only_one_side_has():
    before = record({"a": "Paris", "b": "Tokyo"})
    after = record({"a": "Paris", "b": "Tokyo"})
    after["scores"] = {"a": 1.0, "c": 1.0}
    diff = results.compare(before, after)
    assert diff.only_in_baseline == ("b",)
    assert diff.only_in_candidate == ("c",)
