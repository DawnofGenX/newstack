"""The command line: exit codes are part of the contract."""

import json
from datetime import datetime
from pathlib import Path

from {{ package_name }} import cli

NY = "America/New_York"


def run(capsys, argv):
    code = cli.main(argv)
    return code, capsys.readouterr()


def test_next_prints_the_firings(capsys):
    code, captured = run(
        capsys, ["next", "--rule", "FREQ=DAILY", "--start", "2026-01-01T09:00", "--count", "3"]
    )
    assert code == 0
    assert "2026-01-01 09:00" in captured.out
    assert "stopped    limit 3 reached" in captured.out


def test_next_json_carries_local_and_instant(capsys):
    code, captured = run(
        capsys,
        [
            "next",
            "--rule",
            "FREQ=DAILY",
            "--start",
            "2026-03-07T02:30",
            "--zone",
            NY,
            "--count",
            "2",
            "--json",
        ],
    )
    payload = json.loads(captured.out)
    assert code == 0
    assert payload["occurrences"][0]["local"] == "2026-03-07T02:30:00"
    assert payload["occurrences"][0]["instant"] == "2026-03-07T07:30:00Z"


def test_next_reports_a_skipped_wall_time_in_json(capsys):
    code, captured = run(
        capsys,
        [
            "next",
            "--rule",
            "FREQ=DAILY",
            "--start",
            "2026-03-07T02:30",
            "--zone",
            NY,
            "--count",
            "2",
            "--json",
        ],
    )
    payload = json.loads(captured.out)
    assert code == 0
    assert payload["skipped"][0]["local"] == "2026-03-08T02:30:00"


def test_a_rule_that_cannot_fire_exits_one(capsys):
    code, captured = run(
        capsys,
        [
            "next",
            "--rule",
            "FREQ=YEARLY;BYMONTH=2;BYMONTHDAY=29",
            "--start",
            "2025-03-01T00:00",
            "--span-years",
            "1",
        ],
    )
    assert code == 1
    assert "no occurrence" in captured.out


def test_between_counts_the_window(capsys):
    code, captured = run(
        capsys,
        [
            "between",
            "--rule",
            "FREQ=DAILY",
            "--start",
            "2026-01-01T09:00",
            "--since",
            "2026-01-03T00:00",
            "--until",
            "2026-01-05T12:00",
        ],
    )
    assert code == 0
    assert "firings    3" in captured.out


def test_an_inverted_window_is_a_usage_error(capsys):
    code, captured = run(
        capsys,
        [
            "between",
            "--rule",
            "FREQ=DAILY",
            "--start",
            "2026-01-01T09:00",
            "--since",
            "2026-01-05T00:00",
            "--until",
            "2026-01-03T00:00",
        ],
    )
    assert code == 2
    assert "window is empty" in captured.err


def test_explain_exits_one_when_the_date_is_not_a_firing(capsys):
    code, captured = run(
        capsys,
        [
            "explain",
            "--rule",
            "FREQ=WEEKLY;BYDAY=MO",
            "--start",
            "2026-01-05T09:00",
            "--at",
            "2026-01-07T09:00",
        ],
    )
    assert code == 1
    assert "not an occurrence" in captured.out


def test_explain_exits_zero_when_it_is(capsys):
    code, captured = run(
        capsys,
        [
            "explain",
            "--rule",
            "FREQ=WEEKLY;BYDAY=MO",
            "--start",
            "2026-01-05T09:00",
            "--at",
            "2026-01-12T09:00",
        ],
    )
    assert code == 0
    assert "an occurrence" in captured.out


def test_a_start_with_an_offset_is_refused(capsys):
    code, captured = run(
        capsys,
        ["next", "--rule", "FREQ=DAILY", "--start", "2026-01-01T09:00+00:00", "--count", "1"],
    )
    assert code == 2
    assert "wall time" in captured.err


def test_an_unknown_zone_is_refused(capsys):
    code, captured = run(
        capsys,
        ["next", "--rule", "FREQ=DAILY", "--start", "2026-01-01T09:00", "--zone", "Mars/Olympus"],
    )
    assert code == 2
    assert "not a time zone" in captured.err


def test_a_rule_that_cannot_be_parsed_is_unusable(capsys):
    code, captured = run(
        capsys, ["next", "--rule", "FREQ=SOMETIMES", "--start", "2026-01-01T09:00"]
    )
    assert code == 2
    assert "FREQ" in captured.err


def test_demo_and_selftest_dispatch(capsys):
    parser = cli.build_parser()
    assert parser.parse_args(["demo"]).handler is cli._command_demo
    assert parser.parse_args(["selftest"]).handler is cli._command_selftest


def test_the_fixture_rules_all_expand():
    fixtures = Path(__file__).resolve().parent.parent / "fixtures" / "rules.txt"
    rows = [line for line in fixtures.read_text().splitlines() if line and not line.startswith("#")]
    assert len(rows) == 5
    for row in rows:
        rule_text, start_text, zone, _ = [part.strip() for part in row.split("|")]
        from zoneinfo import ZoneInfo

        from {{ package_name }}.expand import expand
        from {{ package_name }}.rrule import parse

        result = expand(
            parse(rule_text), datetime.fromisoformat(start_text), ZoneInfo(zone), limit=5
        )
        assert result.occurrences, rule_text
