from __future__ import annotations

import json

import pytest

from {{ package_name }} import cli as subject

SPEC = "fixtures/openapi.json"


def test_list_prints_every_operation(capsys) -> None:
    assert subject.main(["--spec", SPEC, "list"]) == subject.EXIT_OK
    out = capsys.readouterr().out
    for operation_id in ("listNotes", "createNote", "getNote"):
        assert operation_id in out


def test_a_conforming_call_exits_zero(capsys, honest_url) -> None:
    assert (
        subject.main(["--spec", SPEC, "--base-url", honest_url, "call", "listNotes"])
        == subject.EXIT_OK
    )
    out = capsys.readouterr().out
    assert out.startswith("200 listNotes")
    assert "first" in out


def test_the_json_flag_prints_only_the_body(capsys, honest_url) -> None:
    assert (
        subject.main(["--spec", SPEC, "--base-url", honest_url, "call", "listNotes", "--json"])
        == subject.EXIT_OK
    )
    body = json.loads(capsys.readouterr().out)
    assert isinstance(body, list) and body[0]["id"] == "1"


def test_a_query_parameter_is_typed_and_sent(capsys, honest_url) -> None:
    assert (
        subject.main(
            ["--spec", SPEC, "--base-url", honest_url, "call", "listNotes", "--param", "limit=2"]
        )
        == subject.EXIT_OK
    )
    assert "limit=2" in capsys.readouterr().out


def test_a_slash_in_a_path_value_is_encoded(capsys, honest_url) -> None:
    assert (
        subject.main(
            [
                "--spec",
                SPEC,
                "--base-url",
                honest_url,
                "call",
                "getNote",
                "--param",
                "id=a/b",
                "--json",
            ]
        )
        == subject.EXIT_OK
    )
    assert json.loads(capsys.readouterr().out)["detail"] == "a%2Fb"


def test_drift_exits_one_and_prints_the_member(capsys, drifted_url) -> None:
    assert (
        subject.main(["--spec", SPEC, "--base-url", drifted_url, "call", "listNotes"])
        == subject.EXIT_DRIFT
    )
    captured = capsys.readouterr()
    assert "drift" in captured.err
    assert "$[0].tags: expected array, got integer" in captured.err


def test_an_unknown_operation_exits_two(capsys, honest_url) -> None:
    assert (
        subject.main(["--spec", SPEC, "--base-url", honest_url, "call", "deleteNote"])
        == subject.EXIT_UNUSABLE
    )
    assert "deleteNote" in capsys.readouterr().err


def test_a_missing_parameter_exits_two(capsys, honest_url) -> None:
    assert (
        subject.main(["--spec", SPEC, "--base-url", honest_url, "call", "getNote"])
        == subject.EXIT_UNUSABLE
    )
    assert "needs --param id" in capsys.readouterr().err


def test_an_undeclared_parameter_exits_two(capsys, honest_url) -> None:
    assert (
        subject.main(
            ["--spec", SPEC, "--base-url", honest_url, "call", "listNotes", "--param", "p9=1"]
        )
        == subject.EXIT_UNUSABLE
    )
    assert "takes no parameter" in capsys.readouterr().err


def test_an_invalid_request_exits_one(capsys, honest_url, tmp_path) -> None:
    body = tmp_path / "bad.json"
    body.write_text('{"tags": []}', encoding="utf-8")
    assert (
        subject.main(
            ["--spec", SPEC, "--base-url", honest_url, "call", "createNote", "--body", str(body)]
        )
        == subject.EXIT_DRIFT
    )
    assert "missing required member 'title'" in capsys.readouterr().err


def test_a_body_from_a_file_is_sent(capsys, honest_url, tmp_path) -> None:
    body = tmp_path / "good.json"
    body.write_text('{"title": "from a file"}', encoding="utf-8")
    assert (
        subject.main(
            ["--spec", SPEC, "--base-url", honest_url, "call", "createNote", "--body", str(body)]
        )
        == subject.EXIT_OK
    )
    assert "from a file" in capsys.readouterr().out


def test_validate_accepts_a_good_response(capsys, tmp_path) -> None:
    response = tmp_path / "good.json"
    response.write_text(
        json.dumps({"id": "1", "title": "x", "tags": [], "pinned": False}), encoding="utf-8"
    )
    assert (
        subject.main(
            ["--spec", SPEC, "validate", "--operation", "getNote", "--response", str(response)]
        )
        == subject.EXIT_OK
    )
    assert "fits" in capsys.readouterr().out


def test_validate_rejects_a_bad_response(capsys, tmp_path) -> None:
    response = tmp_path / "bad.json"
    response.write_text(
        json.dumps({"id": 1, "title": "x", "tags": [], "pinned": False}), encoding="utf-8"
    )
    assert (
        subject.main(
            ["--spec", SPEC, "validate", "--operation", "getNote", "--response", str(response)]
        )
        == subject.EXIT_DRIFT
    )
    assert "$.id: expected string, got integer" in capsys.readouterr().err


def test_a_missing_document_exits_two(capsys, tmp_path) -> None:
    assert subject.main(["--spec", str(tmp_path / "nope.json"), "list"]) == subject.EXIT_UNUSABLE
    assert "cannot read" in capsys.readouterr().err


def test_a_dead_server_exits_two(capsys) -> None:
    assert (
        subject.main(["--spec", SPEC, "--base-url", "http://127.0.0.1:1", "call", "listNotes"])
        == subject.EXIT_UNUSABLE
    )
    assert "cannot reach" in capsys.readouterr().err


def test_version_and_help_are_available(capsys) -> None:
    with pytest.raises(SystemExit) as version:
        subject.main(["--version"])
    assert version.value.code == 0
    assert "newstack-smoke-python-duckdb-report-1793898647" in capsys.readouterr().out
    with pytest.raises(SystemExit) as helped:
        subject.main(["--help"])
    assert helped.value.code == 0
    assert "call" in capsys.readouterr().out
