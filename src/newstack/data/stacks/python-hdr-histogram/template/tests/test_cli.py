"""The command line: exit codes and the files it writes."""

import json
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

import pytest

from {{ package_name }} import cli as subject


def run(argv):
    out, err = StringIO(), StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = subject.main(argv)
    return code, out.getvalue(), err.getvalue()


def fixtures(name="latencies.jsonl"):
    from pathlib import Path

    return str(Path(__file__).resolve().parent.parent / "fixtures" / name)


def test_a_percentile_run_reports_and_exits_zero():
    code, out, _ = run(["percentile", "--input", fixtures(), "--p", "50,99"])
    assert code == 0
    assert "reported" in out
    assert "within the promise" in out


def test_the_json_form_carries_every_percentile():
    code, out, _ = run(["percentile", "--input", fixtures(), "--p", "50,99", "--json"])
    assert code == 0
    payload = json.loads(out)
    assert [row["p"] for row in payload["percentiles"]] == [50.0, 99.0]
    assert payload["held"] is True
    assert payload["samples"] == 240


def test_recording_writes_a_histogram(tmp_path):
    where = tmp_path / "histogram.json"
    code, out, _ = run(["record", "--input", fixtures(), "--out", str(where)])
    assert code == 0
    assert where.exists()
    assert "samples      240" in out
    payload = json.loads(where.read_text("utf-8"))
    assert payload["type"] == "hdr-histogram"
    assert payload["total"] == 240


def test_info_describes_a_stored_histogram(tmp_path):
    where = tmp_path / "histogram.json"
    run(["record", "--input", fixtures(), "--out", str(where)])
    code, out, _ = run(["info", "--histogram", str(where)])
    assert code == 0
    assert "p99" in out
    assert "byte(s)" in out


def test_two_halves_merge_into_the_whole(tmp_path):
    source = tmp_path / "latencies.jsonl"
    rows = [str(value) for value in range(1, 501)]
    source.write_text("\n".join(rows) + "\n", "utf-8")
    left_file, right_file = tmp_path / "left.json", tmp_path / "right.json"
    (tmp_path / "a.jsonl").write_text("\n".join(rows[:250]) + "\n", "utf-8")
    (tmp_path / "b.jsonl").write_text("\n".join(rows[250:]) + "\n", "utf-8")
    run(["record", "--input", str(tmp_path / "a.jsonl"), "--out", str(left_file)])
    run(["record", "--input", str(tmp_path / "b.jsonl"), "--out", str(right_file)])
    code, out, _ = run(["merge", "--left", str(left_file), "--right", str(right_file)])
    assert code == 0
    assert "merged       500 sample(s)" in out


def test_a_missing_input_is_a_usage_error():
    code, _, err = run(["percentile", "--input", "/nonexistent/latencies.jsonl"])
    assert code == 2
    assert "no such file" in err


def test_an_empty_input_is_refused(tmp_path):
    where = tmp_path / "empty.jsonl"
    where.write_text("\n", "utf-8")
    code, _, err = run(["percentile", "--input", str(where)])
    assert code == 2
    assert "no latencies" in err


def test_an_unreadable_percentile_is_refused():
    code, _, err = run(["percentile", "--input", fixtures(), "--p", "fifty"])
    assert code == 2
    assert "not a percentile" in err


def test_a_foreign_histogram_file_is_refused(tmp_path):
    where = tmp_path / "histogram.json"
    where.write_text('{"type": "something-else"}\n', "utf-8")
    code, _, err = run(["info", "--histogram", str(where)])
    assert code == 2
    assert "not a histogram" in err


def test_no_command_prints_help_and_exits_two():
    code, out, _ = run([])
    assert code == 2
    assert "percentile" in out


def test_the_parser_routes_selftest_without_running_it():
    assert subject.build_parser().parse_args(["selftest"]).handler is subject._command_selftest


def test_version_prints_the_program_name():
    with pytest.raises(SystemExit) as raised:
        run(["--version"])
    assert raised.value.code == 0
