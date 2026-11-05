"""The report is the deliverable, so its shape and its honesty are tested."""

from __future__ import annotations

from {{ package_name }}.evaluate import Report, evaluate
from {{ package_name }}.qrels import Qrels


def test_every_query_is_scored(report: Report, qrels: Qrels) -> None:
    assert len(report.scores) == len(qrels.queries)
    assert [score.query for score in report.scores] == sorted(qrels.queries)


def test_a_query_without_judgements_is_skipped_not_failed(report: Report) -> None:
    assert report.skipped == 1
    assert report.judged == len(report.scores) - 1
    skipped = [score for score in report.scores if score.relevant == 0]
    assert skipped[0].recall is None


def test_the_shipped_corpus_is_retrievable(report: Report) -> None:
    assert report.macro("recall") >= 0.8
    assert 0.0 <= report.micro_recall <= 1.0


def test_macro_and_micro_are_both_reported(report: Report) -> None:
    payload = report.as_dict()
    assert payload["macro_recall"] == round(report.macro("recall"), 4)
    assert payload["micro_recall"] == round(report.micro_recall, 4)


def test_the_report_records_the_settings_that_produced_it(report: Report) -> None:
    payload = report.as_dict()
    assert payload["k"] == report.k
    assert payload["size"] == report.size
    assert payload["overlap"] == report.overlap
    assert payload["chunks"] == report.chunks


def test_changing_the_window_changes_the_chunk_count(
    corpus: dict[str, str], qrels: Qrels, report: Report
) -> None:
    smaller = evaluate(corpus, qrels.queries, size=20, overlap=0, k=qrels.k)
    assert smaller.chunks > report.chunks


def test_k_must_be_positive(corpus: dict[str, str], qrels: Qrels) -> None:
    import pytest

    with pytest.raises(ValueError):
        evaluate(corpus, qrels.queries, k=0)
