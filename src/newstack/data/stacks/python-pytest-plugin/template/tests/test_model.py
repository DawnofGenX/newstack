"""The report format is the contract between the plugin and the CLI."""

import json
from pathlib import Path

import pytest

from {{ package_name }} import model as subject


def record(nodeid: str = "tests/test_x.py::test_one", **extra: object) -> subject.TestRecord:
    fields: dict[str, object] = {"nodeid": nodeid, "outcome": "passed", "duration_ms": 1.5}
    fields.update(extra)
    return subject.TestRecord(**fields)  # type: ignore[arg-type]


def test_counts_name_every_outcome() -> None:
    report = subject.Report(0, (record(), record("tests/test_x.py::test_two", outcome="skipped")))
    assert report.counts() == {"passed": 1, "failed": 0, "skipped": 1, "error": 0}


def test_slowest_orders_by_duration_then_nodeid() -> None:
    report = subject.Report(
        0,
        (
            record("b", duration_ms=10.0),
            record("a", duration_ms=10.0),
            record("c", duration_ms=20.0),
        ),
    )
    assert [test.nodeid for test in report.slowest(2)] == ["c", "a"]


def test_gate_is_strictly_greater() -> None:
    report = subject.Report(0, (record(duration_ms=250.0),))
    assert report.over(250.0) == []
    assert [test.nodeid for test in report.over(249.9)] == ["tests/test_x.py::test_one"]


def test_slowest_phase_names_the_expensive_one() -> None:
    test = record(
        phases={"setup": subject.Phase("passed", 1.0), "call": subject.Phase("passed", 9.0)}
    )
    assert test.slowest_phase() == "call"
    assert record().slowest_phase() == "-"


def test_ticket_falls_back_to_a_dash() -> None:
    assert record().ticket == "-"
    assert record(tickets=("ABC-1", "ABC-2")).ticket == "ABC-1"


def test_dict_round_trip_keeps_phases() -> None:
    report = subject.Report(
        2, (record(phases={"call": subject.Phase("failed", 3.25)}, tickets=("ABC-1",)),)
    )
    back = subject.Report.from_dict(json.loads(json.dumps(report.as_dict())))
    assert back.exit_status == 2
    assert back.tests[0].phases["call"] == subject.Phase("failed", 3.25)
    assert back.tests[0].tickets == ("ABC-1",)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ([], "must be a JSON object"),
        ({"format": 2, "exit_status": 0, "tests": []}, "unsupported report format 2"),
        ({"format": 1, "exit_status": 0}, "no tests list"),
        (
            {"format": 1, "exit_status": 0, "tests": [{"outcome": "passed", "duration_ms": 1}]},
            "has no nodeid",
        ),
        (
            {
                "format": 1,
                "exit_status": 0,
                "tests": [{"nodeid": "t", "outcome": "flaky", "duration_ms": 1}],
            },
            "expected one of",
        ),
        (
            {
                "format": 1,
                "exit_status": 0,
                "tests": [{"nodeid": "t", "outcome": "passed", "duration_ms": True}],
            },
            "no numeric duration_ms",
        ),
    ],
)
def test_bad_reports_are_refused_with_a_reason(payload: object, message: str) -> None:
    with pytest.raises(subject.InputError, match=message):
        subject.Report.from_dict(payload)


def test_save_and_load_agree(tmp_path: Path) -> None:
    path = tmp_path / "report.json"
    subject.save(path, subject.Report(0, (record(tickets=("ABC-4",)),)))
    loaded = subject.load(path)
    assert loaded.as_dict() == subject.Report(0, (record(tickets=("ABC-4",)),)).as_dict()


def test_load_explains_what_is_wrong(tmp_path: Path) -> None:
    missing = tmp_path / "absent.json"
    with pytest.raises(subject.InputError, match="cannot read"):
        subject.load(missing)
    broken = tmp_path / "broken.json"
    broken.write_text("{nope")
    with pytest.raises(subject.InputError, match="is not JSON"):
        subject.load(broken)
