import pytest

from {{ package_name }} import conditions


def test_equal_operands_hold():
    outcome = conditions.evaluate(
        {"left": "$resource.owner", "op": "eq", "right": "$subject.id"},
        {"id": "bob"},
        {"owner": "bob"},
    )
    assert outcome.satisfied
    assert "==" in outcome.reason


def test_different_operands_do_not_hold():
    outcome = conditions.evaluate(
        {"left": "$resource.owner", "op": "eq", "right": "$subject.id"},
        {"id": "bob"},
        {"owner": "dave"},
    )
    assert not outcome.satisfied


def test_a_missing_attribute_is_not_a_match():
    outcome = conditions.evaluate(
        {"left": "$resource.owner", "op": "eq", "right": "$subject.id"},
        {"id": "bob"},
        {},
    )
    assert not outcome.satisfied
    assert "missing" in outcome.reason


def test_a_literal_right_operand_is_allowed():
    outcome = conditions.evaluate(
        {"left": "$resource.classification", "op": "neq", "right": "secret"},
        {},
        {"classification": "public"},
    )
    assert outcome.satisfied


def test_in_takes_a_list():
    outcome = conditions.evaluate(
        {"left": "$subject.team", "op": "in", "right": ["core", "platform"]},
        {"team": "platform"},
        {},
    )
    assert outcome.satisfied


def test_numeric_comparisons_compare_numbers():
    outcome = conditions.evaluate(
        {"left": "$resource.size", "op": "lt", "right": "10"},
        {},
        {"size": "9"},
    )
    assert outcome.satisfied


def test_a_non_number_is_an_error_not_a_false():
    with pytest.raises(conditions.ConditionError):
        conditions.evaluate(
            {"left": "$resource.size", "op": "lt", "right": "10"},
            {},
            {"size": "big"},
        )


def test_present_and_absent():
    assert conditions.evaluate(
        {"left": "$resource.owner", "op": "present"}, {}, {"owner": "bob"}
    ).satisfied
    assert conditions.evaluate({"left": "$resource.owner", "op": "absent"}, {}, {}).satisfied


def test_an_unknown_operator_is_refused():
    with pytest.raises(conditions.ConditionError):
        conditions.evaluate({"left": "a", "op": "roughly", "right": "b"}, {}, {})


def test_an_unknown_field_is_refused():
    with pytest.raises(conditions.ConditionError):
        conditions.evaluate({"left": "a", "op": "eq", "rght": "b"}, {}, {})


def test_no_condition_always_holds():
    assert conditions.evaluate(None, {}, {}).satisfied


def test_an_operand_must_name_a_namespace():
    with pytest.raises(conditions.ConditionError):
        conditions.evaluate({"left": "$owner", "op": "eq", "right": "bob"}, {}, {})
