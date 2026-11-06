from __future__ import annotations

import pytest

from {{ package_name }} import dfa as engine
from {{ package_name }} import nfa as nfa_module
from {{ package_name }} import syntax


def test_the_start_state_is_the_closure_of_the_nfa_start() -> None:
    automaton = engine.determinize(syntax.parse("a*"))
    assert automaton.start == 0
    assert 0 in automaton.accepting


def test_every_transition_lands_on_a_known_state() -> None:
    automaton = engine.determinize(syntax.parse("(a|b)*abb"))
    for source, symbol, target in automaton.transitions:
        assert 0 <= source < automaton.states
        assert 0 <= target < automaton.states
        assert isinstance(symbol, str)


def test_an_unmentioned_character_folds_into_one_symbol() -> None:
    automaton = engine.determinize(syntax.parse("ab"))
    assert automaton.symbol_for("Q") == automaton.other
    assert automaton.symbol_for("a") == "a"


def test_running_the_dfa_is_one_lookup_per_character() -> None:
    automaton = engine.determinize(syntax.parse("(a|b)*abb"))
    path = automaton.run("ababb")
    assert len(path) == 6
    assert path[-1] in automaton.accepting


@pytest.mark.parametrize(
    ("pattern", "alphabet", "longest"),
    [
        ("(a|b)*abb", "ab", 6),
        ("a*b", "ab", 5),
        ("(cat|dog)s?", "catsdog", 4),
        ("[a-c]+", "abc", 4),
        ("a?b?c?", "abc", 3),
        ("(ab|ba)+", "ab", 5),
    ],
)
def test_both_machines_agree_on_every_short_string(
    pattern: str, alphabet: str, longest: int
) -> None:
    verdict = engine.agreement(syntax.parse(pattern), alphabet=alphabet, longest=longest)
    assert verdict.held(), verdict.mismatches
    assert verdict.checked == sum(len(alphabet) ** length for length in range(longest + 1))


def test_the_agreement_report_says_how_much_it_checked() -> None:
    verdict = engine.agreement(syntax.parse("a*b"), alphabet="ab", longest=4)
    assert verdict.checked == 31
    assert "checked" in "\n".join(verdict.lines())


def test_a_disagreement_would_be_reported() -> None:
    fake = engine.Agreement(pattern="a", alphabet="a", longest=1, checked=2, mismatches=("a",))
    assert not fake.held()
    assert "DISAGREE" in fake.lines()[-2]


def test_the_dfa_is_smaller_than_the_power_set() -> None:
    node = syntax.parse("(a|b)*abb")
    automaton = engine.determinize(node)
    assert automaton.states < 2 ** nfa_module.compile_node(node).states


def test_a_huge_enumeration_is_refused_rather_than_attempted() -> None:
    with pytest.raises(ValueError, match="past the"):
        engine._strings("abcdefghi", 12)


def test_the_dfa_accepts_the_same_language_as_a_single_run() -> None:
    node = syntax.parse("(ab|cd)*e?")
    automaton = engine.determinize(node)
    for text in ["", "ab", "abcd", "ababcde", "abx"]:
        assert automaton.matches(text) == nfa_module.compile_node(node).matches(text)
