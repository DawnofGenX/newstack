"""Every metric here has a wrong version that looks plausible; the tests name it."""

from __future__ import annotations

import pytest

from {{ package_name }} import metrics as subject


def test_repeated_chunks_of_one_document_count_once() -> None:
    assert subject.ranked_documents(["a#0", "a#30", "b#0"]) == ["a", "b"]


def test_recall_is_a_share_of_the_relevant_documents() -> None:
    assert subject.recall_at_k(["a", "b"], {"a", "c"}, 1) == 0.5
    assert subject.recall_at_k(["a"], {"a"}, 3) == 1.0


def test_recall_is_none_when_nothing_is_relevant() -> None:
    assert subject.recall_at_k(["a"], set(), 3) is None


def test_precision_divides_by_k_not_by_the_number_returned() -> None:
    assert subject.precision_at_k(["a"], {"a"}, 2) == 0.5
    assert subject.precision_at_k(["a"], {"a"}, 1) == 1.0


def test_reciprocal_rank_uses_the_first_hit_only() -> None:
    assert subject.reciprocal_rank(["x", "a"], {"a"}) == 0.5
    assert subject.reciprocal_rank(["a", "x"], {"a"}) == 1.0
    assert subject.reciprocal_rank(["x"], {"a"}) == 0.0


def test_ndcg_is_one_for_a_perfect_ordering() -> None:
    assert subject.ndcg_at_k(["a", "b"], {"a": 2, "b": 1}, 2) == pytest.approx(1.0)


def test_ndcg_rewards_higher_grades_first() -> None:
    ordered = subject.ndcg_at_k(["a", "b"], {"a": 2, "b": 1}, 2)
    swapped = subject.ndcg_at_k(["b", "a"], {"a": 2, "b": 1}, 2)
    assert 0.0 < swapped < ordered


def test_a_document_judged_zero_is_not_a_relevant_result() -> None:
    grades = {"x": 0}
    relevant = {doc_id for doc_id, grade in grades.items() if grade > 0}
    assert relevant == set()
    assert subject.recall_at_k(["x"], relevant, 1) is None
    assert subject.ndcg_at_k(["x"], grades, 1) == 0.0


def test_mean_reports_how_many_values_it_skipped() -> None:
    assert subject.mean([1.0, None, 0.0]) == (0.5, 1)
    assert subject.mean([]) == (0.0, 0)


def test_dcg_discounts_by_position() -> None:
    assert subject.dcg([1, 1]) > subject.dcg([1, 0])
