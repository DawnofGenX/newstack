from __future__ import annotations

import pytest

from {{ package_name }} import schema as subject

NOTE = {"$ref": "#/components/schemas/Note"}

GOOD = {
    "id": "1",
    "title": "first",
    "tags": ["a"],
    "pinned": False,
    "body": None,
    "priority": "normal",
}


def test_python_types_map_to_json_types() -> None:
    assert subject.type_name(None) == "null"
    assert subject.type_name(True) == "boolean"
    assert subject.type_name(1) == "integer"
    assert subject.type_name(1.5) == "number"
    assert subject.type_name("x") == "string"
    assert subject.type_name([]) == "array"
    assert subject.type_name({}) == "object"


def test_a_bool_is_not_an_integer(spec) -> None:
    # True == 1 in Python, so this is the trap a naive validator falls into.
    assert subject.validate(True, {"type": "integer"}, spec.document) == [
        "$: expected integer, got boolean"
    ]
    assert subject.validate(1, {"type": "boolean"}, spec.document) == [
        "$: expected boolean, got integer"
    ]


def test_a_valid_note_has_no_problems(spec) -> None:
    assert subject.validate(GOOD, NOTE, spec.document) == []


def test_a_null_member_is_allowed_by_a_type_list(spec) -> None:
    assert subject.validate(GOOD, NOTE, spec.document) == []
    assert subject.validate({**GOOD, "body": "text"}, NOTE, spec.document) == []


def test_a_wrong_type_names_the_member(spec) -> None:
    assert subject.validate({**GOOD, "tags": 7}, NOTE, spec.document) == [
        "$.tags: expected array, got integer"
    ]


def test_a_nested_problem_carries_its_index(spec) -> None:
    problems = subject.validate({**GOOD, "tags": [1]}, NOTE, spec.document)
    assert problems == ["$.tags[0]: expected string, got integer"]


def test_an_undeclared_member_is_reported_when_the_schema_forbids_it(spec) -> None:
    problems = subject.validate({**GOOD, "server_side": True}, NOTE, spec.document)
    assert problems == ["$: unexpected member 'server_side'"]


def test_an_extra_member_is_fine_when_the_schema_allows_it() -> None:
    # `additionalProperties` defaults to allowing anything; only `false` forbids it.
    permissive = {"type": "object", "properties": {"error": {"type": "string"}}}
    assert subject.validate({"error": "x", "extra": 1}, permissive, {}) == []


def test_a_missing_required_member_is_reported(spec) -> None:
    problems = subject.validate({"id": "1", "tags": [], "pinned": False}, NOTE, spec.document)
    assert "$: missing required member 'title'" in problems


def test_an_enum_rejects_a_value_it_never_listed(spec) -> None:
    problems = subject.validate({**GOOD, "priority": "urgent"}, NOTE, spec.document)
    assert problems == ["$.priority: 'urgent' is not one of 'high', 'low', 'normal'"]


def test_an_enum_does_not_confuse_true_with_one() -> None:
    assert not subject.same_value(True, 1)
    document: dict = {}
    assert subject.validate(True, {"enum": [1]}, document) == ["$: True is not one of 1"]


def test_length_and_bounds_are_enforced(spec) -> None:
    empty_title = {"title": ""}
    assert subject.validate(
        empty_title, {"$ref": "#/components/schemas/NoteInput"}, spec.document
    ) == ["$.title: shorter than 1 characters"]
    too_big = subject.validate(
        101, {"type": "integer", "minimum": 1, "maximum": 100}, spec.document
    )
    assert too_big == ["$: 101 is above the maximum 100"]


def test_nullable_is_understood_as_the_older_spelling(spec) -> None:
    assert subject.validate(None, {"type": "string", "nullable": True}, spec.document) == []


def test_a_local_reference_that_is_missing_is_an_error(spec) -> None:
    with pytest.raises(subject.SchemaError):
        subject.resolve(spec.document, "#/components/schemas/Nope")
    with pytest.raises(subject.SchemaError):
        subject.resolve(spec.document, "https://example.com/schema.json")


def test_anyof_accepts_either_branch() -> None:
    schema = {"anyOf": [{"type": "string"}, {"type": "integer"}]}
    assert subject.validate("x", schema, {}) == []
    assert subject.validate(3, schema, {}) == []
    assert subject.validate([], schema, {}) == ["$: matches none of the anyOf schemas"]
