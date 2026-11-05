import json
from pathlib import Path

import pytest

from {{ package_name }} import cli as subject
from {{ package_name }} import events as events_mod

BASE = 1_767_225_600 * events_mod.US


def write(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "events.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    return path


def stamp(seconds: int) -> str:
    return events_mod.to_iso(BASE + seconds * events_mod.US)


@pytest.mark.parametrize(
    ("text", "micros"),
    [
        ("60", 60 * events_mod.US),
        ("5m", 300 * events_mod.US),
        ("500ms", 500_000),
        ("1h", 3600 * events_mod.US),
    ],
)
def test_durations(text: str, micros: int) -> None:
    assert subject.parse_duration(text) == micros


def test_a_negative_duration_is_refused() -> None:
    import argparse

    with pytest.raises(argparse.ArgumentTypeError):
        subject.parse_duration("-5s")


def test_run_exits_zero(tmp_path: Path) -> None:
    path = write(tmp_path, [{"t": stamp(1), "value": 1}, {"t": stamp(2), "value": 2}])
    assert subject.main(["run", "--events", str(path), "--agg", "sum"]) == subject.EXIT_OK


def test_late_data_exits_one(tmp_path: Path) -> None:
    path = write(tmp_path, [{"t": stamp(300), "value": 1}, {"t": stamp(1), "value": 1}])
    assert subject.main(["run", "--events", str(path)]) == subject.EXIT_LATE


def test_a_missing_file_exits_two(tmp_path: Path) -> None:
    missing = tmp_path / "absent.jsonl"
    assert subject.main(["run", "--events", str(missing)]) == subject.EXIT_UNUSABLE


def test_a_naive_timestamp_exits_two(tmp_path: Path) -> None:
    path = write(tmp_path, [{"t": "2026-01-01T00:00:00", "value": 1}])
    assert subject.main(["run", "--events", str(path)]) == subject.EXIT_UNUSABLE


def test_the_json_report_is_written(tmp_path: Path) -> None:
    path = write(tmp_path, [{"t": stamp(1), "value": 1}])
    out = tmp_path / "report.json"
    assert subject.main(["run", "--events", str(path), "--json", str(out)]) == subject.EXIT_OK
    assert json.loads(out.read_text())["windows"][0]["count"] == 1


def test_demo_runs() -> None:
    assert subject.main(["demo"]) == subject.EXIT_OK


def test_no_command_prints_help() -> None:
    assert subject.main([]) == subject.EXIT_UNUSABLE
