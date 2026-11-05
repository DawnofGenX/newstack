from __future__ import annotations

from pathlib import Path

import pytest

from {{ package_name }} import spec as subject

SPEC_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "openapi.json"


def test_the_document_names_its_operations(spec) -> None:
    assert sorted(spec.operations) == ["createNote", "getNote", "listNotes"]
    assert spec.base_url == "http://127.0.0.1:5473"


def test_the_method_and_path_survive(spec) -> None:
    operation = spec.operation("getNote")
    assert (operation.method, operation.path) == ("GET", "/notes/{id}")


def test_an_unknown_operation_lists_what_is_available(spec) -> None:
    with pytest.raises(subject.SpecError) as caught:
        spec.operation("deleteNote")
    assert "deleteNote" in str(caught.value) and "listNotes" in str(caught.value)


def test_an_operation_without_an_id_cannot_be_called_by_name() -> None:
    document = {"paths": {"/x": {"get": {"responses": {}}}}}
    with pytest.raises(subject.SpecError, match="operationId"):
        subject.operations_of(document)


def test_a_repeated_id_is_refused() -> None:
    document = {
        "paths": {
            "/a": {"get": {"operationId": "same", "responses": {}}},
            "/b": {"get": {"operationId": "same", "responses": {}}},
        }
    }
    with pytest.raises(subject.SpecError, match="used twice"):
        subject.operations_of(document)


def test_a_document_without_paths_is_refused() -> None:
    with pytest.raises(subject.SpecError, match="no paths"):
        subject.operations_of({"openapi": "3.1.0"})


def test_a_non_openapi_document_is_refused(tmp_path) -> None:
    broken = tmp_path / "swagger.json"
    broken.write_text('{"swagger": "2.0", "paths": {}}', encoding="utf-8")
    with pytest.raises(subject.SpecError, match="OpenAPI 3"):
        subject.load(broken)


def test_malformed_json_is_reported_with_a_line(tmp_path) -> None:
    broken = tmp_path / "bad.json"
    broken.write_text('{"openapi": "3.1.0",', encoding="utf-8")
    with pytest.raises(subject.SpecError, match="line 1"):
        subject.load(broken)


def test_a_path_value_is_percent_encoded(spec) -> None:
    operation = spec.operation("getNote")
    base = "http://127.0.0.1:5473"
    assert subject.build_url(base, operation, {"id": "a/b"}) == "http://127.0.0.1:5473/notes/a%2Fb"
    assert (
        subject.build_url(base, operation, {"id": "a?b=c"})
        == "http://127.0.0.1:5473/notes/a%3Fb%3Dc"
    )
    assert subject.build_url(base, operation, {"id": "ü"}) == "http://127.0.0.1:5473/notes/%C3%BC"


def test_a_query_value_is_encoded_and_optional(spec) -> None:
    base = "http://127.0.0.1:5473"
    assert subject.build_url(base, spec.operation("listNotes"), {}) == "http://127.0.0.1:5473/notes"
    assert (
        subject.build_url(base, spec.operation("listNotes"), {"limit": 5})
        == "http://127.0.0.1:5473/notes?limit=5"
    )


def test_a_parameter_the_document_never_declared_is_refused(spec) -> None:
    with pytest.raises(subject.SpecError, match="takes no parameter"):
        subject.build_url(
            "http://127.0.0.1:5473", spec.operation("listNotes"), {"limit": 1, "offset": 2}
        )


def test_a_missing_required_parameter_is_refused(spec) -> None:
    with pytest.raises(subject.SpecError, match="needs --param id"):
        subject.build_url("http://127.0.0.1:5473", spec.operation("getNote"), {})


def test_text_is_coerced_by_the_declared_type(spec) -> None:
    assert subject.coerce("12", {"type": "integer"}) == 12
    assert subject.coerce("-1.5", {"type": "number"}) == -1.5
    assert subject.coerce("no", {"type": "boolean"}) is False
    assert subject.coerce("x", {"type": "string"}) == "x"
    with pytest.raises(subject.SpecError, match="expected an integer"):
        subject.coerce("twelve", {"type": "integer"})
    with pytest.raises(subject.SpecError, match="expected a boolean"):
        subject.coerce("maybe", {"type": "boolean"})
