import json

import pytest

from {{ package_name }} import cli as subject


def history_file(tmp_path, rows, initial=0):
    path = tmp_path / "history.jsonl"
    lines = [json.dumps({"initial": initial})]
    lines.extend(json.dumps(row) for row in rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write(client, value, start, end):
    return {"client": client, "op": "write", "value": value, "start": start, "end": end}


def read(client, value, start, end):
    return {"client": client, "op": "read", "value": value, "start": start, "end": end}


def test_a_linearizable_history_exits_zero(tmp_path, capsys):
    path = history_file(tmp_path, [write(0, 5, 0, 1), read(0, 5, 2, 3)])
    assert subject.main(["check", "--history", str(path)]) == 0
    assert "verdict    linearizable" in capsys.readouterr().out


def test_a_refused_history_exits_one(tmp_path, capsys):
    path = history_file(tmp_path, [write(0, 5, 0, 2), read(1, 0, 3, 4)])
    assert subject.main(["check", "--history", str(path)]) == 1
    assert "not linearizable" in capsys.readouterr().out


def test_json_carries_the_order(tmp_path, capsys):
    path = history_file(tmp_path, [write(0, 5, 0, 1), read(0, 5, 2, 3)])
    assert subject.main(["check", "--history", str(path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["linearizable"] is True
    assert payload["order"] == [0, 1]
    assert payload["initial"] == 0


def test_the_initial_value_can_be_overridden(tmp_path):
    path = history_file(tmp_path, [read(0, 7, 0, 1)])
    assert subject.main(["check", "--history", str(path)]) == 1
    assert subject.main(["check", "--history", str(path), "--initial", "7"]) == 0


def test_a_missing_file_exits_two(tmp_path, capsys):
    assert subject.main(["check", "--history", str(tmp_path / "nope.jsonl")]) == 2
    assert "no such history" in capsys.readouterr().err


def test_a_broken_line_exits_two(tmp_path, capsys):
    path = tmp_path / "broken.jsonl"
    path.write_text("{oops\n", encoding="utf-8")
    assert subject.main(["check", "--history", str(path)]) == 2
    assert "not JSON" in capsys.readouterr().err


def test_shrink_prints_the_core(tmp_path, capsys):
    rows = [write(0, 1, 0, 1), read(1, 0, 2, 3), write(2, 9, 4, 5), read(1, 9, 6, 7)]
    path = history_file(tmp_path, rows)
    assert subject.main(["shrink", "--history", str(path)]) == 1
    out = capsys.readouterr().out
    assert "core" in out and "of 4 operation(s)" in out


def test_shrinking_a_good_history_says_so(tmp_path, capsys):
    path = history_file(tmp_path, [read(0, 0, 0, 1)])
    assert subject.main(["shrink", "--history", str(path)]) == 0
    assert "nothing to shrink" in capsys.readouterr().out


def test_compare_agrees_with_itself(tmp_path, capsys):
    rows = [write(0, 1, 0, 1), read(1, 1, 2, 3), write(2, 2, 2, 4), read(3, 2, 5, 6)]
    path = history_file(tmp_path, rows)
    assert subject.main(["compare", "--history", str(path)]) == 0
    assert "the two checkers agree" in capsys.readouterr().out


def test_compare_refuses_a_history_it_cannot_enumerate(tmp_path, capsys):
    rows = [read(0, 0, index, index + 1) for index in range(9)]
    path = history_file(tmp_path, rows)
    assert subject.main(["compare", "--history", str(path)]) == 2
    assert "stops at 8" in capsys.readouterr().err


def test_demo_exits_zero(capsys):
    assert subject.main(["demo"]) == 0
    assert "stories      6 of 6 hold" in capsys.readouterr().out


def test_selftest_exits_zero(capsys):
    assert subject.main(["selftest"]) == 0
    assert "0 failed" in capsys.readouterr().out


def test_version_and_help_follow_the_program_name(capsys):
    with pytest.raises(SystemExit) as raised:
        subject.main(["--version"])
    assert raised.value.code == 0
    assert subject.PROGRAM in capsys.readouterr().out
