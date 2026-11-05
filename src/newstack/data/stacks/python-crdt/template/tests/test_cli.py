import json
from pathlib import Path

import pytest

from {{ package_name }} import cli as subject
from {{ package_name }} import orset


def test_the_demo_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["demo"]) == 0
    assert "gossip" in capsys.readouterr().out


def test_the_law_report_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["laws"]) == 0
    output = capsys.readouterr().out
    assert "laws: all held" in output
    assert "or-set" in output


def test_no_subcommand_exits_two(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main([]) == 2
    assert "choose one of" in capsys.readouterr().err


def test_merge_reads_two_files(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    left = tmp_path / "left.json"
    right = tmp_path / "right.json"
    left.write_text(json.dumps({"type": "g-counter", "counts": {"a": 2}}), encoding="utf-8")
    right.write_text(json.dumps({"type": "g-counter", "counts": {"b": 3}}), encoding="utf-8")
    assert subject.main(["merge", str(left), str(right)]) == 0
    merged = json.loads(capsys.readouterr().out)
    assert merged == {"type": "g-counter", "counts": {"a": 2, "b": 3}}


def test_merge_refuses_two_lattices(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    left = tmp_path / "left.json"
    right = tmp_path / "right.json"
    left.write_text(json.dumps({"type": "g-counter", "counts": {"a": 2}}), encoding="utf-8")
    right.write_text(json.dumps(orset.ORSet().add("x", "a").as_dict()), encoding="utf-8")
    assert subject.main(["merge", str(left), str(right)]) == 2
    assert "different lattices" in capsys.readouterr().err


def test_merge_refuses_an_unknown_type(tmp_path: Path) -> None:
    left = tmp_path / "left.json"
    left.write_text(json.dumps({"type": "signed-total"}), encoding="utf-8")
    assert subject.main(["merge", str(left), str(left)]) == 2


def test_a_missing_file_exits_two(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    left = tmp_path / "left.json"
    left.write_text(json.dumps({"type": "g-counter", "counts": {}}), encoding="utf-8")
    assert subject.main(["merge", str(left), str(tmp_path / "absent.json")]) == 2
    assert "cannot read" in capsys.readouterr().err


def test_broken_json_exits_two(tmp_path: Path) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    assert subject.main(["merge", str(broken), str(broken)]) == 2


def test_a_state_that_is_not_an_object_is_refused(tmp_path: Path) -> None:
    payload = tmp_path / "list.json"
    payload.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(subject.UsageError):
        subject.load_state(payload)


def test_the_version_flag_names_the_program(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        subject.main(["--version"])
    assert raised.value.code == 0
    assert subject.PROGRAM in capsys.readouterr().out
