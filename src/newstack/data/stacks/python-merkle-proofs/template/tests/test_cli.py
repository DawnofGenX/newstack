"""The command line: exit codes are the contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from {{ package_name }} import cli as subject

ROOT_FIVE = "d8fdb1f0c326081f8917ea62b5551153f7f2ad06edf53202861eb36afe8f360d"
FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "entries.txt"


def test_root_prints_the_root_of_a_leaf_file(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["root", "--leaves", str(FIXTURE)]) == subject.EXIT_OK
    output = capsys.readouterr().out
    assert ROOT_FIVE in output
    assert "size         5" in output


def test_root_json_has_the_size_and_the_root(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["root", "--leaves", str(FIXTURE), "--json"]) == subject.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"size": 5, "root": ROOT_FIVE}


def test_prove_writes_a_proof_that_verifies(tmp_path: Path,
                                           capsys: pytest.CaptureFixture[str]) -> None:
    proof_path = tmp_path / "proof.json"
    assert subject.main(["prove", "--leaves", str(FIXTURE), "--index", "3",
                         "--json"]) == subject.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    proof_path.write_text(json.dumps(payload))
    assert payload["index"] == 3
    assert payload["size"] == 5
    assert len(payload["path"]) == 3
    capsys.readouterr()
    code = subject.main(["verify", "--leaf", "entry-04", "--proof", str(proof_path)])
    assert code == subject.EXIT_OK
    assert "recomputes the root" in capsys.readouterr().out


def test_verify_refuses_a_changed_leaf(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["prove", "--leaves", str(FIXTURE), "--index", "3",
                         "--json"]) == subject.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    path = ",".join(payload["path"])
    code = subject.main(["verify", "--leaf", "entry-99", "--index", "3", "--size", "5",
                         "--root", ROOT_FIVE, "--path", path])
    assert code == subject.EXIT_REFUSED
    assert "refused" in capsys.readouterr().out


def test_verify_accepts_an_honest_path(capsys: pytest.CaptureFixture[str]) -> None:
    subject.main(["prove", "--leaves", str(FIXTURE), "--index", "0", "--json"])
    payload = json.loads(capsys.readouterr().out)
    code = subject.main(["verify", "--leaf", "entry-01", "--index", "0", "--size", "5",
                         "--root", ROOT_FIVE, "--path", ",".join(payload["path"])])
    assert code == subject.EXIT_OK


def test_a_proof_file_and_an_index_cannot_both_be_given(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = subject.main(["verify", "--leaf", "entry-04", "--index", "2",
                         "--proof", str(FIXTURE.parent.parent / "proof-that-does-not-exist")])
    assert code == subject.EXIT_UNUSABLE
    assert "contradicts --proof" in capsys.readouterr().err


def test_verify_wants_a_path_or_a_proof(capsys: pytest.CaptureFixture[str]) -> None:
    code = subject.main(["verify", "--leaf", "entry-01", "--index", "0", "--size", "5",
                         "--root", ROOT_FIVE])
    assert code == subject.EXIT_UNUSABLE
    assert "needs --path or --proof" in capsys.readouterr().err


def test_a_missing_file_is_a_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    code = subject.main(["root", "--leaves", "/nonexistent/leaves.txt"])
    assert code == subject.EXIT_UNUSABLE
    assert "does not exist" in capsys.readouterr().err


def test_an_empty_leaf_file_is_a_usage_error(tmp_path: Path,
                                             capsys: pytest.CaptureFixture[str]) -> None:
    empty = tmp_path / "empty.txt"
    empty.write_text("\n\n")
    assert subject.main(["root", "--leaves", str(empty)]) == subject.EXIT_UNUSABLE
    assert "nothing to prove" in capsys.readouterr().err


def test_an_index_past_the_end_is_a_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["prove", "--leaves", str(FIXTURE), "--index", "9"]) == (
        subject.EXIT_UNUSABLE
    )
    assert "not in a tree" in capsys.readouterr().err


def test_a_proof_file_that_is_not_json_is_a_usage_error(tmp_path: Path,
                                                       capsys: pytest.CaptureFixture[str]) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text("{not json")
    assert subject.main(["verify", "--leaf", "a", "--proof", str(broken)]) == (
        subject.EXIT_UNUSABLE
    )
    assert "is not JSON" in capsys.readouterr().err


def test_demo_exits_zero_and_prints_every_story(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["demo"]) == subject.EXIT_OK
    output = capsys.readouterr().out
    assert output.count("-> holds") == 6
    assert "domain prefix" in output


def test_selftest_is_reachable_from_the_command_line(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert subject.main(["selftest"]) == subject.EXIT_OK
    assert "checks passed" in capsys.readouterr().out


def test_version_and_help_do_not_need_a_command(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as version:
        subject.main(["--version"])
    assert version.value.code == 0
    assert "{{ npm_name }}" in capsys.readouterr().out
    with pytest.raises(SystemExit) as help_exit:
        subject.main(["--help"])
    assert help_exit.value.code == 0
    assert "Merkle" in capsys.readouterr().out
