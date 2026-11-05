import pytest

from {{ package_name }} import harness
from {{ package_name }}.dataset import Example

EXAMPLES = [
    Example(id="a", prompt="q", gold="Paris"),
    Example(id="b", prompt="q", gold="Tokyo"),
    Example(id="c", prompt="q", gold="4"),
]


def test_a_perfect_run_scores_one():
    report = harness.evaluate(EXAMPLES, {"a": "Paris", "b": "Tokyo", "c": "4"})
    assert report.score == 1.0
    assert report.answered == 3
    assert report.missing == ()


def test_a_missing_prediction_scores_zero_instead_of_disappearing():
    report = harness.evaluate(EXAMPLES, {"a": "Paris"})
    assert report.total == 3
    assert report.answered == 1
    assert report.missing == ("b", "c")
    assert report.score == pytest.approx(1 / 3)


def test_predictions_for_ids_that_are_not_in_the_data_are_reported_not_scored():
    report = harness.evaluate(EXAMPLES, {"a": "Paris", "b": "Tokyo", "c": "4", "ghost": "x"})
    assert report.unused == ("ghost",)
    assert "ghost" not in report.scores


def test_the_metric_is_selectable_and_recorded():
    report = harness.evaluate(EXAMPLES, {"a": "Paris.", "b": "Tokyo, Japan"}, metric="exact_match")
    assert report.metric == "exact_match"
    assert report.scores["a"] == 1.0  # normalisation makes "Paris." the same answer
    assert report.scores["b"] == 0.0  # "Tokyo, Japan" is not exactly "Tokyo"


def test_summary_rounds_the_score_and_sorts_the_scores():
    report = harness.evaluate(EXAMPLES, {"a": "Paris", "b": "Tokyo", "c": "5"})
    summary = report.summary()
    assert summary["score"] == pytest.approx(0.666667)
    assert list(summary["scores"]) == ["a", "b", "c"]
    assert summary["answered"] == 3
