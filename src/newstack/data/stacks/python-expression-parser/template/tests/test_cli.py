import json
import subprocess
import sys
from pathlib import Path

from {{ package_name }} import cli


def run(argv):
    return cli.main(argv)


def test_a_value_is_printed(capsys):
    assert run(["eval", "2 + 3 * 4"]) == 0
    out = capsys.readouterr().out
    assert "value      14" in out
    assert "mode       exact" in out


def test_a_rounded_value_says_so(capsys):
    assert run(["eval", "1 / 3", "--inexact"]) == 0
    out = capsys.readouterr().out
    assert "rounded to" in out


def test_an_inexact_answer_without_the_flag_is_refused(capsys):
    assert run(["eval", "1 / 3"]) == cli.EXIT_REFUSED
    assert "no finite decimal expansion" in capsys.readouterr().err


def test_a_broken_expression_is_unusable(capsys):
    assert run(["eval", "2 + * 3"]) == cli.EXIT_UNUSABLE
    err = capsys.readouterr().err
    assert "column 5" in err
    assert "^" in err


def test_parse_prints_the_tree(capsys):
    assert run(["parse", "2 + 3 * 4"]) == 0
    out = capsys.readouterr().out
    assert "render     2 + 3 * 4" in out
    assert "tree" in out


def test_parse_json_carries_the_shape(capsys):
    assert run(["parse", "2 * 3", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["tree"]["kind"] == "binary"
    assert payload["tree"]["op"] == "*"


def test_eval_json_carries_the_mode(capsys):
    assert run(["eval", "8 / 2", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["value"] == "4"
    assert payload["exact"] is True


def test_a_variable_can_be_given(capsys):
    assert run(["eval", "x * 2", "--var", "x=21"]) == 0
    assert "value      42" in capsys.readouterr().out


def test_a_bad_variable_is_a_usage_error(capsys):
    assert run(["eval", "x", "--var", "x"]) == cli.EXIT_UNUSABLE
    assert "name=value" in capsys.readouterr().err


def test_explain_shows_the_table(capsys):
    assert run(["explain", "2 ^ 3 ^ 2"]) == 0
    out = capsys.readouterr().out
    assert "precedence" in out
    assert "value      512" in out


def test_demo_holds(capsys):
    assert run(["demo"]) == 0
    assert "6 of 6 hold" in capsys.readouterr().out


def test_selftest_passes(capsys):
    assert run(["selftest"]) == 0
    assert "0 failed" in capsys.readouterr().out


def test_the_module_entry_point_runs():
    project = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "{{ package_name }}",
            "eval",
            "1 + 1",
        ],
        cwd=project,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "value      2" in result.stdout


def test_version_names_the_program(capsys):
    try:
        run(["--version"])
    except SystemExit as exit:
        assert exit.code == 0
    assert cli.PROGRAM in capsys.readouterr().out
