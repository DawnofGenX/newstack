"""The command line: identifiers, decoding, and the audit gate."""

import json
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

from {{ package_name }} import cli as subject
from {{ package_name }} import layout


def run(argv):
    out, err = StringIO(), StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = subject.main(argv)
    return code, out.getvalue(), err.getvalue()


def test_generate_prints_identifiers_and_exits_zero():
    code, out, _ = run(["generate", "--count", "3", "--worker", "4"])
    assert code == 0
    assert "issued       3 identifier(s) from worker 4" in out


def test_generate_json_carries_the_identifiers():
    code, out, _ = run(["generate", "--count", "2", "--worker", "4", "--json"])
    assert code == 0
    payload = json.loads(out)
    assert len(payload["ids"]) == 2
    assert payload["stats"]["worker"] == 4


def test_a_single_millisecond_run_exhausts_the_sequence():
    code, out, _ = run(["generate", "--count", "4100", "--worker", "1"])
    assert code == 0
    assert "waits        1" in out


def test_decode_reads_one_identifier():
    value = layout.compose(1_000, 3, 7)
    code, out, _ = run(["decode", str(value)])
    assert code == 0
    assert "worker 3" in out
    assert "sequence 7" in out


def test_capacity_names_the_fields():
    code, out, _ = run(["capacity"])
    assert code == 0
    assert "worker" in out
    assert "layout ends" in out


def test_a_missing_audit_file_is_unusable_input():
    code, _, err = run(["audit", "--input", "/nonexistent/ids.jsonl"])
    assert code == 2
    assert "no such file" in err


def test_an_empty_audit_file_is_unusable_input(tmp_path):
    where = tmp_path / "ids.jsonl"
    where.write_text("\n", "utf-8")
    code, _, err = run(["audit", "--input", str(where)])
    assert code == 2
    assert "no identifiers" in err


def test_a_broken_stream_exits_one(tmp_path):
    where = tmp_path / "ids.jsonl"
    value = layout.compose(10, 1, 0)
    where.write_text(f"{value}\n{value}\n", "utf-8")
    code, out, _ = run(["audit", "--input", str(where)])
    assert code == 1
    assert "BROKEN" in out


def test_a_clean_stream_exits_zero(tmp_path):
    where = tmp_path / "ids.jsonl"
    rows = [str(layout.compose(10 + step, 1, 0)) for step in range(4)]
    where.write_text("\n".join(rows) + "\n", "utf-8")
    code, out, _ = run(["audit", "--input", str(where)])
    assert code == 0
    assert "sound" in out


def test_an_unreadable_worker_is_unusable_input():
    code, _, err = run(["generate", "--count", "1", "--worker", "2048"])
    assert code == 2
    assert "worker" in err


def test_a_bad_count_is_unusable_input():
    code, _, err = run(["generate", "--count", "many"])
    assert code == 2
    assert "whole number" in err


def test_no_command_prints_help_and_exits_two():
    code, out, _ = run([])
    assert code == 2
    assert "generate" in out


def test_the_parser_routes_selftest():
    assert subject.build_parser().parse_args(["selftest"]).handler is subject._command_selftest
