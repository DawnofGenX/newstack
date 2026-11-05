import pytest

from {{ package_name }} import metrics


def test_normalize_hides_case_punctuation_and_whitespace():
    assert metrics.normalize("  Paris,  FRANCE! ") == "paris france"


def test_exact_match_ignores_case_and_a_trailing_full_stop():
    assert metrics.exact_match("Paris.", "paris") == 1.0
    assert metrics.exact_match("Lyon", "Paris") == 0.0


def test_token_f1_is_symmetric_on_a_shared_set():
    long, short = "the quick brown fox", "quick brown fox"
    assert metrics.token_f1(long, short) == pytest.approx(0.8571, abs=1e-4)
    assert metrics.token_f1(short, long) == pytest.approx(0.8571, abs=1e-4)


def test_token_f1_counts_multisets_so_repetition_cannot_be_farmed():
    # "paris paris paris" has three of the one gold token: precision 1/3.
    assert metrics.token_f1("paris paris paris", "paris") == pytest.approx(0.5, abs=1e-4)


def test_token_f1_without_overlap_is_zero():
    assert metrics.token_f1("kyoto", "tokyo") == 0.0


def test_empty_strings_score_zero_instead_of_dividing_by_zero():
    assert metrics.token_f1("", "paris") == 0.0
    assert metrics.token_f1("paris", "") == 0.0
    assert metrics.exact_match("", "") == 1.0


def test_contains_is_substring_recall_and_is_lenient_on_purpose():
    assert metrics.contains("Tokyo, Japan", "Tokyo") == 1.0
    assert metrics.contains("not Paris, it is Lyon", "Paris") == 1.0
    assert metrics.contains("Lyon", "Paris") == 0.0


def test_get_names_the_metric_it_did_not_recognise():
    with pytest.raises(KeyError, match="unknown metric 'bleu'"):
        metrics.get("bleu")
