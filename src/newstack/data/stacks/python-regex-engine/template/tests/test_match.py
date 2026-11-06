from __future__ import annotations

from {{ package_name }} import backtrack, syntax
from {{ package_name }} import match as engine


def test_a_whole_match_needs_the_whole_text() -> None:
    assert engine.full(syntax.parse("ab"), "ab") == "ab"
    assert engine.full(syntax.parse("ab"), "abc") is None
    assert engine.full(syntax.parse("ab"), "") is None


def test_search_finds_the_leftmost_run() -> None:
    found = engine.search(syntax.parse("a+"), "xaay")
    assert found is not None
    assert (found.start, found.end, found.value) == (1, 3, "aa")


def test_search_takes_the_longest_end_at_the_first_start() -> None:
    found = engine.search(syntax.parse("ab|abc"), "zabc")
    assert found is not None
    assert found.value == "abc"
    assert found.length == 3


def test_search_reports_a_span_into_the_original_text() -> None:
    found = engine.search(syntax.parse("dog"), "the dog barks")
    assert found is not None
    assert found.text[found.start : found.end] == "dog"


def test_a_pattern_that_matches_nothing_finds_nothing() -> None:
    assert engine.search(syntax.parse("z"), "banana") is None


def test_a_pattern_that_can_match_nothing_matches_at_zero() -> None:
    found = engine.search(syntax.parse("a*"), "bbb")
    assert found is not None
    assert found.length == 0
    assert found.start == 0


def test_every_non_overlapping_match_is_reported() -> None:
    found = engine.all_matches(syntax.parse("a"), "banana")
    assert [item.start for item in found] == [1, 3, 5]


def test_an_empty_match_still_moves_the_search_forward() -> None:
    found = engine.all_matches(syntax.parse("b*"), "ab")
    assert len(found) >= 2
    assert found[0].start == 0


def test_the_description_names_both_questions() -> None:
    lines = engine.describe(syntax.parse("a+"), "xaay")
    assert any(line.startswith("whole") for line in lines)
    assert any(line.startswith("match") for line in lines)


def test_the_backtracker_answers_correctly() -> None:
    node = syntax.parse("(a|b)*abb")
    for text in ["ababb", "abba", "abb"]:
        steps = backtrack.count(node, text)
        assert steps.matched == engine.full_matches(node, text)


def test_the_backtracker_is_exponential_on_a_nested_star() -> None:
    node = syntax.parse("(a*)*b")
    short = backtrack.count(node, "a" * 10)
    longer = backtrack.count(node, "a" * 14)
    assert not short.matched
    assert not longer.matched
    assert longer.steps > 4 * short.steps


def test_a_budget_stops_the_backtracker_and_says_so() -> None:
    steps = backtrack.count(syntax.parse("(a*)*b"), "a" * 40, cap=500)
    assert steps.capped
    assert steps.steps <= 600


def test_the_simulation_never_needs_more_than_one_pass() -> None:
    node = syntax.parse("(a*)*b")
    text = "a" * 20
    steps = backtrack.count(node, text)
    assert steps.steps > 1000
    assert len(text) + 1 < steps.steps // 100
