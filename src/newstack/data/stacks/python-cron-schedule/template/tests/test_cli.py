import json

import pytest

from {{ package_name }} import cli as subject
from {{ package_name }} import demo as demo_mod


def run(capsys, *argv):
    status = subject.main(list(argv))
    captured = capsys.readouterr()
    return status, captured.out, captured.err


def test_next_prints_the_utc_instant_and_the_wall_clock(capsys):
    status, out, err = run(
        capsys,
        "next",
        "30 2 * * *",
        "--after",
        "2026-03-07T12:00:00Z",
        "--tz",
        "America/New_York",
        "--count",
        "2",
    )
    assert status == subject.EXIT_OK
    assert "2026-03-09T06:30:00Z  = 2026-03-09 02:30 EDT  America/New_York" in out
    assert err == ""


def test_next_defaults_to_now_in_utc(capsys):
    status, out, _err = run(capsys, "next", "* * * * *", "--count", "1")
    assert status == subject.EXIT_OK
    assert "zone     UTC" in out


def test_next_json_carries_the_raw_instants(capsys):
    status, out, _err = run(
        capsys, "next", "0 0 1 * *", "--after", "2026-03-02T00:00:00Z", "--json"
    )
    payload = json.loads(out)
    assert status == subject.EXIT_OK
    assert payload["runs"][0]["utc"] == "2026-04-01T00:00:00+00:00"
    assert payload["zone"] == "UTC"


def test_a_schedule_that_never_fires_exits_one(capsys):
    status, _out, err = run(capsys, "next", "0 0 30 2 *", "--after", "2026-03-02T00:00:00Z")
    assert status == subject.EXIT_NOTHING
    assert "describes nothing" in err


def test_explain_says_which_rule_joined_the_day_fields(capsys):
    status, out, _err = run(capsys, "explain", "0 0 1 * 1")
    assert status == subject.EXIT_OK
    assert "day rule   or" in out
    assert "expression 0 0 1 * 1" in out


def test_explain_marks_the_plain_case(capsys):
    _status, out, _err = run(capsys, "explain", "0 9 * * mon-fri")
    assert "day rule   and" in out
    assert "weekday    1,2,3,4,5" in out


@pytest.mark.parametrize(
    ("argv", "fragment"),
    [
        (("next", "* * * *", "--after", "2026-03-02T00:00:00Z"), "five fields"),
        (("next", "60 * * * *"), "outside 0-59"),
        (("next", "* * * * *", "--after", "2026-03-02T00:00:00"), "has no offset"),
        (("next", "* * * * *", "--after", "tuesday"), "not an ISO 8601 moment"),
        (("next", "* * * * *", "--tz", "Mars/Olympus"), "unknown time zone"),
    ],
)
def test_unusable_input_exits_two(capsys, argv, fragment):
    status, out, err = run(capsys, *argv)
    assert status == subject.EXIT_UNUSABLE
    assert fragment in err
    assert out == ""


def test_demo_runs_and_reports_each_scenario(capsys):
    status, out, _err = run(capsys, "demo")
    assert status == subject.EXIT_OK
    assert "six" not in out
    assert "the hour that never happens" in out
    assert "demo: 6 schedules, 0 not as advertised" in out


def test_demo_exits_one_when_a_claim_breaks(capsys, monkeypatch):
    broken = demo_mod.Step("a broken claim", ("nothing",), False)
    monkeypatch.setattr(demo_mod, "run", lambda: [broken])
    status, out, _err = run(capsys, "demo")
    assert status == subject.EXIT_NOTHING
    assert "NOT AS ADVERTISED" in out


def test_selftest_passes(capsys):
    status, out, _err = run(capsys, "selftest")
    assert status == subject.EXIT_OK
    assert "0 failed" in out


def test_version_and_help(capsys):
    with pytest.raises(SystemExit) as version:
        subject.main(["--version"])
    assert version.value.code == 0
    assert subject.PROGRAM in capsys.readouterr().out
    with pytest.raises(SystemExit) as usage:
        subject.main([])
    assert usage.value.code == 2
