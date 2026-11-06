"""The command line: exit codes are the contract, so they are what is tested."""

import json
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

import pytest

from {{ package_name }} import cli as subject


def run(argv, capsys=None):
    """Capture the console only: stdout.write stays untouched for the reporter."""
    out, err = StringIO(), StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = subject.main(argv)
    return code, out.getvalue(), err.getvalue()


def test_an_ordered_pair_exits_zero():
    code, out, _ = run(["compare", "--left", "a:1", "--right", "a:2"])
    assert code == 0
    assert "relation     before" in out


def test_a_concurrent_pair_exits_one():
    code, out, _ = run(["compare", "--left", "a:1", "--right", "b:1"])
    assert code == 1
    assert "relation     concurrent" in out
    assert "neither write saw the other" in out


def test_an_equal_pair_says_so():
    code, out, _ = run(["compare", "--left", "a:2,b:1", "--right", "b:1,a:2"])
    assert code == 0
    assert "relation     equal" in out


def test_compare_prints_json_on_request():
    code, out, _ = run(["compare", "--left", "a:1", "--right", "a:2", "--json"])
    assert code == 0
    payload = json.loads(out)
    assert payload["relation"] == "before"
    assert payload["left"] == "a:1"


def test_merge_prints_the_join():
    code, out, _ = run(["merge", "--left", "a:2", "--right", "b:3"])
    assert code == 0
    assert "merged       a:2,b:3" in out
    assert "the merge is after both: True" in out


@pytest.mark.parametrize(
    ("vector", "floor", "code", "needle"),
    [
        ("a:4,b:2", "a:3,b:2", 0, "sound        yes"),
        ("a:2,b:2", "a:3,b:2", 1, "sound        NO"),
    ],
)
def test_prune_gates_on_the_floor(vector, floor, code, needle):
    result, out, _ = run(["prune", "--vector", vector, "--floor", floor])
    assert result == code
    assert needle in out


def test_prune_reports_what_it_dropped():
    _, out, _ = run(["prune", "--vector", "a:4,b:2", "--floor", "a:3,b:2"])
    assert "compacted    a:4 (1 entries)" in out
    assert "dropped      1" in out


def test_pairs_prints_a_matrix(tmp_path):
    where = tmp_path / "vectors.jsonl"
    where.write_text('{"name": "x", "vector": "a:1"}\n{"name": "y", "vector": "b:1"}\n', "utf-8")
    code, out, _ = run(["pairs", "--vectors", str(where)])
    assert code == 1
    assert "legend" in out
    assert "concurrent    1 pair(s) out of 1" in out


def test_a_consistent_file_exits_zero(tmp_path):
    where = tmp_path / "vectors.jsonl"
    where.write_text('{"name": "x", "vector": "a:1"}\n{"name": "y", "vector": "a:2"}\n', "utf-8")
    code, out, _ = run(["pairs", "--vectors", str(where)])
    assert code == 0
    assert "concurrent    0 pair(s) out of 1" in out


def test_an_empty_vector_file_is_refused(tmp_path):
    where = tmp_path / "empty.jsonl"
    where.write_text("\n", "utf-8")
    code, _, err = run(["pairs", "--vectors", str(where)])
    assert code == 2
    assert "holds no vectors" in err


def test_a_missing_file_is_refused():
    code, _, err = run(["pairs", "--vectors", "/nonexistent/vectors.jsonl"])
    assert code == 2
    assert "no such file" in err


def test_a_bad_vector_is_a_usage_error():
    code, _, err = run(["compare", "--left", "a", "--right", "a:1"])
    assert code == 2
    assert "the form is name:count" in err


def test_an_unknown_command_is_argparse_territory():
    with pytest.raises(SystemExit):
        run(["order", "--left", "a:1"])


def test_no_command_prints_help_and_exits_two():
    code, out, _ = run([])
    assert code == 2
    assert "compare" in out


def test_the_parser_routes_selftest_without_running_it():
    assert subject.build_parser().parse_args(["selftest"]).handler is subject._command_selftest
    assert subject.build_parser().parse_args(["demo"]).handler is subject._command_demo


def test_version_prints_the_program_name():
    with pytest.raises(SystemExit) as raised:
        run(["--version"])
    assert raised.value.code == 0
