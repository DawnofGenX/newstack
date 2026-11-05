import json
from pathlib import Path

import pytest

from {{ package_name }} import schema as subject


def test_a_document_that_matches_has_no_problems(v1: dict) -> None:
    document = {"id": "ord_1", "type": "order.created", "amount": 5, "status": "pending"}
    assert subject.validate(v1, v1, document) == []


def test_every_problem_is_reported_not_just_the_first(v1: dict) -> None:
    problems = subject.validate(v1, v1, {"amount": -1, "status": "lost"})
    assert any("missing required member 'id'" in problem for problem in problems)
    assert any("missing required member 'type'" in problem for problem in problems)
    assert any("below the minimum" in problem for problem in problems)
    assert any("'lost' is not one of" in problem for problem in problems)


def test_a_type_mismatch_names_both_types(v1: dict) -> None:
    problems = subject.validate(
        v1, v1, {"id": "ord_1", "type": "order.created", "amount": "5", "status": "pending"}
    )
    assert problems == ["$.amount: expected integer, got string"]


def test_a_wrong_document_shape_stops_at_the_type(v1: dict) -> None:
    problems = subject.validate(v1, v1, [1, 2, 3])
    assert problems == ["$: expected object, got array"]


def test_an_undeclared_member_is_allowed_when_the_schema_is_open(v1: dict) -> None:
    document = {
        "id": "ord_1",
        "type": "order.created",
        "amount": 1,
        "status": "paid",
        "extra": True,
    }
    assert subject.validate(v1, v1, document) == []


def test_an_undeclared_member_is_refused_when_the_schema_is_closed(v2: dict) -> None:
    document = {
        "id": "ord_1",
        "type": "order.created",
        "amount": 1,
        "status": "paid",
        "currency": "USD",
        "extra": True,
    }
    assert subject.validate(v2, v2, document) == ["$.extra: unexpected member 'extra'"]


def test_an_additional_properties_schema_validates_the_member() -> None:
    document = {
        "$schema": subject.INPUT_VERSION,
        "type": "object",
        "additionalProperties": {"type": "integer"},
    }
    assert subject.validate(document, document, {"a": "1"}) == ["$.a: expected integer, got string"]


def test_a_null_is_not_a_string_where_a_union_is_declared(v1: dict) -> None:
    document = {"id": "ord_1", "type": "order.created", "amount": 1, "status": "paid", "note": None}
    assert subject.validate(v1, v1, document) == []
    document["note"] = 5
    assert subject.validate(v1, v1, document) == ["$.note: expected null, string, got integer"]


def test_an_integer_satisfies_a_number() -> None:
    assert subject.matches_type(3, "number")
    assert not subject.matches_type(True, "integer")
    assert subject.type_name(True) == "boolean"


def test_an_array_is_validated_item_by_item(v1: dict) -> None:
    document = {
        "id": "ord_1",
        "type": "order.created",
        "amount": 1,
        "status": "paid",
        "tags": ["ok", 4],
    }
    assert subject.validate(v1, v1, document) == ["$.tags[1]: expected string, got integer"]


def test_a_local_ref_is_followed() -> None:
    document = {
        "$schema": subject.INPUT_VERSION,
        "$defs": {"amount": {"type": "integer", "minimum": 1}},
        "type": "object",
        "properties": {"total": {"$ref": "#/$defs/amount"}},
    }
    problems = subject.validate(document, document, {"total": 0})
    assert problems == ["$.total: below the minimum 1"]


def test_a_remote_ref_is_refused() -> None:
    with pytest.raises(subject.SchemaError, match="only local"):
        subject.resolve({"a": {}}, "https://example.com/schema.json")


def test_a_ref_that_points_nowhere_is_named() -> None:
    with pytest.raises(subject.SchemaError, match=r"\$ref '#/nope' does not resolve"):
        subject.resolve({"a": {}}, "#/nope")


def test_a_deep_ref_chain_is_refused() -> None:
    document = {"a": {"$ref": "#/b"}, "b": {"$ref": "#/a"}}
    with pytest.raises(subject.SchemaError, match="too deep"):
        subject.deref(document, {"$ref": "#/a"})


def test_a_file_without_a_schema_key_is_not_a_schema(tmp_path: Path) -> None:
    sample = tmp_path / "sample.json"
    sample.write_text(json.dumps({"id": 1}))
    with pytest.raises(subject.SchemaError, match=r"has no \$schema"):
        subject.load(sample)


def test_broken_json_names_the_file(tmp_path: Path) -> None:
    sample = tmp_path / "broken.json"
    sample.write_text("{")
    with pytest.raises(subject.SchemaError, match="is not JSON"):
        subject.load(sample)


def test_a_non_object_schema_is_refused(tmp_path: Path) -> None:
    sample = tmp_path / "list.json"
    sample.write_text("[]")
    with pytest.raises(subject.SchemaError, match="is not a JSON object"):
        subject.load(sample)


def test_a_missing_file_names_the_path(tmp_path: Path) -> None:
    with pytest.raises(subject.SchemaError, match="cannot read"):
        subject.load(tmp_path / "missing.json")
