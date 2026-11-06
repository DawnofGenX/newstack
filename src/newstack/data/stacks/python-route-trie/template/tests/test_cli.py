import json
import subprocess
import sys
from pathlib import Path

from {{ package_name }} import cli as subject

PROJECT = Path(__file__).resolve().parent.parent
ROUTES = PROJECT / "fixtures" / "routes.txt"


def run(*args):
    return subject.main(list(args))


def test_a_literal_match_exits_zero(capsys):
    assert run("match", "--routes", str(ROUTES), "--path", "/users/me") == 0
    out = capsys.readouterr().out
    assert "verdict    matched" in out
    assert "route      GET /users/me" in out


def test_a_parameter_match_shows_the_value(capsys):
    assert run("match", "--routes", str(ROUTES), "--path", "/users/42") == 0
    assert "param      id = '42'" in capsys.readouterr().out


def test_a_miss_exits_one(capsys):
    assert run("match", "--routes", str(ROUTES), "--path", "/nowhere") == 1
    assert "verdict    no route" in capsys.readouterr().out


def test_a_wrong_method_exits_one_and_lists_allow(capsys):
    assert run("match", "--routes", str(ROUTES), "--method", "PATCH", "--path", "/users/42") == 1
    assert "allow      DELETE, GET, PUT" in capsys.readouterr().out


def test_the_payload_is_json(capsys):
    assert run("match", "--routes", str(ROUTES), "--path", "/files/a/b.txt", "--json") == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["params"] == {"rest": "a/b.txt"}


def test_the_table_lists_every_route(capsys):
    assert run("table", "--routes", str(ROUTES)) == 0
    out = capsys.readouterr().out
    assert out.startswith("10 route(s)")
    assert "POST" in out


def test_the_table_as_json_is_a_list(capsys):
    assert run("table", "--routes", str(ROUTES), "--json") == 0
    assert len(json.loads(capsys.readouterr().out)) == 10


def test_why_names_the_other_method(capsys):
    assert run("why", "--routes", str(ROUTES), "--method", "PATCH", "--path", "/users/42") == 1
    out = capsys.readouterr().out
    assert "verdict    not-allowed" in out
    assert "GET" in out


def test_why_on_a_match_exits_one(capsys):
    assert run("why", "--routes", str(ROUTES), "--path", "/users/me") == 1
    assert "is served by GET /users/me" in capsys.readouterr().out


def test_a_missing_table_is_unusable(capsys):
    assert run("match", "--routes", "/nope.txt", "--path", "/") == 2
    assert "no such route table" in capsys.readouterr().err


def test_a_malformed_line_is_unusable(tmp_path, capsys):
    broken = tmp_path / "routes.txt"
    broken.write_text("GET /a extra\n")
    assert run("match", "--routes", str(broken), "--path", "/a") == 2
    assert "a route line is" in capsys.readouterr().err


def test_an_empty_table_is_unusable(tmp_path, capsys):
    empty = tmp_path / "routes.txt"
    empty.write_text("# nothing here\n")
    assert run("match", "--routes", str(empty), "--path", "/") == 2
    assert "holds no routes" in capsys.readouterr().err


def test_demo_holds(capsys):
    assert run("demo") == 0
    assert "stories      6 of 6 hold" in capsys.readouterr().out


def test_selftest_passes():
    assert run("selftest") == 0


def test_version_names_the_program():
    result = subprocess.run(
        [sys.executable, "-m", "{{ package_name }}", "--version"],
        cwd=PROJECT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert subject.PROGRAM in result.stdout


def test_an_unknown_method_on_the_command_line_is_unusable(capsys):
    assert run("match", "--routes", str(ROUTES), "--method", "TRACE", "--path", "/") == 2
    assert "not a method this router knows" in capsys.readouterr().err
