from __future__ import annotations

import pytest

from {{ package_name }} import nfa as engine
from {{ package_name }} import syntax


def machine(pattern: str) -> engine.Nfa:
    return engine.compile_node(syntax.parse(pattern))


def test_one_literal_is_two_states_and_one_edge() -> None:
    single = machine("a")
    assert single.states == 2
    assert single.edge_count() == 1
    assert single.epsilon_count() == 0


def test_the_accept_state_has_no_outgoing_edge() -> None:
    for pattern in ["a", "a*", "(a|b)+", "(ab)*c", "a?b?"]:
        assert machine(pattern).accept_is_final(), pattern


def test_concatenation_chains_fragments_with_silent_edges() -> None:
    chained = machine("abc")
    assert chained.states == 6
    assert chained.epsilon_count() == 2


def test_a_star_has_the_silent_way_past_the_loop() -> None:
    star = machine("a*")
    assert star.matches("")
    assert star.matches("aaaa")
    assert not star.matches("b")


def test_a_plus_needs_one_pass_through_the_body() -> None:
    plus = machine("a+")
    assert not plus.matches("")
    assert plus.matches("a")


def test_an_optional_body_can_be_skipped() -> None:
    optional = machine("ab?c")
    assert optional.matches("ac")
    assert optional.matches("abc")
    assert not optional.matches("abbc")


def test_the_run_is_one_state_set_per_character() -> None:
    star = machine("a*")
    assert len(star.run("aaa")) == 4
    assert all(isinstance(states, frozenset) for states in star.run("aaa"))


def test_the_start_set_already_closes_over_silent_edges() -> None:
    star = machine("a*")
    assert star.accepts(star.start_states())


def test_a_dead_branch_leaves_an_empty_set() -> None:
    assert machine("abc").step(machine("abc").start_states(), "z") == frozenset()


def test_the_longest_accepted_prefix_is_reported() -> None:
    assert machine("(cat|dog)s?").accepts_prefix("dogg") == 3
    assert machine("(cat|dog)s?").accepts_prefix("cat") == 3
    assert machine("z").accepts_prefix("abc") is None


def test_dot_matches_exactly_one_character() -> None:
    dot = machine(".")
    assert dot.matches("x")
    assert not dot.matches("")
    assert not dot.matches("xy")


def test_a_class_matches_every_member_and_nothing_else() -> None:
    letters = machine("[a-c]+")
    assert letters.matches("abcba")
    assert not letters.matches("abd")


def test_a_negated_class_matches_what_it_excludes() -> None:
    rest = machine("[^0-9]+")
    assert rest.matches("abc")
    assert not rest.matches("ab1")


def test_alternation_carries_both_options_at_once() -> None:
    choice = machine("(cat|dog)")
    sets = choice.run("c")
    assert len(sets[1]) >= 2


@pytest.mark.parametrize(
    ("pattern", "text", "expected"),
    [
        ("a*b", "aaab", True),
        ("a*b", "aaa", False),
        ("(a|b)*abb", "ababb", True),
        ("(a|b)*abb", "abba", False),
        ("(ab)+", "abab", True),
        ("(ab)+", "aba", False),
    ],
)
def test_whole_text_matching(pattern: str, text: str, expected: bool) -> None:
    assert machine(pattern).matches(text) is expected
