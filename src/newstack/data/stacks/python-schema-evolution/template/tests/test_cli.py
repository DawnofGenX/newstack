import json
from pathlib import Path

import pytest

from {{ package_name }} import cli as subject


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str]:
    status = subject.main(list(argv))
    captured = capsys.readouterr()
    return status, captured.out + captured.err


def test_a_breaking_change_exits_one(capsys: pytest.CaptureFixture[str]) -> None:
    status, output = run(capsys, "diff")
    assert status == subject.EXIT_BREAKING
    assert "breaking required-added" in output
    assert "5 breaking, 0 risky, 1 safe -> breaking" in output


def test_a_compatible_change_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    status, output = run(capsys, "diff", "--new", "fixtures/v3.json")
    assert status == subject.EXIT_OK
    assert "no change" not in output
    assert "0 breaking, 0 risky, 3 safe -> compatible" in output


def test_a_risky_change_passes_until_strict_is_asked(capsys: pytest.CaptureFixture[str]) -> None:
    status, output = run(capsys, "diff", "--new", "fixtures/v4.json")
    assert status == subject.EXIT_OK
    assert "-> risky" in output
    strict, _ = run(capsys, "diff", "--new", "fixtures/v4.json", "--strict")
    assert strict == subject.EXIT_BREAKING


def test_the_json_report_is_machine_readable(capsys: pytest.CaptureFixture[str]) -> None:
    status, output = run(capsys, "diff", "--json")
    payload = json.loads(output)
    assert status == subject.EXIT_BREAKING
    assert payload["verdict"] == "breaking"
    assert payload["counts"] == {"breaking": 5, "risky": 0, "safe": 1}
    assert {finding["rule"] for finding in payload["findings"]} >= {
        "required-added",
        "property-removed",
    }


def test_a_missing_schema_exits_two(capsys: pytest.CaptureFixture[str]) -> None:
    status, output = run(capsys, "diff", "--new", "fixtures/nope.json")
    assert status == subject.EXIT_UNUSABLE
    assert "cannot read" in output


def test_a_document_instead_of_a_schema_exits_two(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    sample = tmp_path / "sample.json"
    sample.write_text(json.dumps({"id": 1}))
    status, output = run(capsys, "diff", "--old", str(sample))
    assert status == subject.EXIT_UNUSABLE
    assert "has no $schema" in output


def test_the_demo_proves_the_breaking_claims(capsys: pytest.CaptureFixture[str]) -> None:
    status, output = run(capsys, "demo")
    assert status == subject.EXIT_OK
    assert "breaking additional-properties-closed" in output
    assert "extra-member.json" in output
    assert (
        "proof    4 validator claim(s) shown by a real document, 1 reader claim(s), 0 unproven"
        in output
    )


def test_the_selftest_passes(capsys: pytest.CaptureFixture[str]) -> None:
    status, output = run(capsys, "selftest")
    assert status == subject.EXIT_OK
    assert "0 failed" in output


def test_version_and_help_exit_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as version:
        subject.main(["--version"])
    assert version.value.code == 0
    with pytest.raises(SystemExit) as usage:
        subject.main([])
    assert usage.value.code == 2


def test_no_command_is_a_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        subject.main([])
    captured = capsys.readouterr()
    assert "required" in captured.err
