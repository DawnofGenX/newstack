"""Offline checks: the report format and the summary, without running pytest."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from . import model, plugin


class Checks:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def ok(self, name: str, condition: bool, detail: str = "") -> None:
        if condition:
            self.passed += 1
            print(f"ok    {name}")
        else:
            self.failed += 1
            print(f"FAIL  {name}{'' if not detail else f'  ({detail})'}")

    def equal(self, name: str, want: object, got: object) -> None:
        self.ok(name, want == got, f"want {want!r}, got {got!r}")

    def raises(self, name: str, error_type: type[BaseException], call) -> None:
        try:
            call()
        except error_type:
            self.ok(name, True)
        except Exception as unexpected:
            self.ok(name, False, f"raised {type(unexpected).__name__}: {unexpected}")
        else:
            self.ok(name, False, "nothing was raised")


def sample_report() -> model.Report:
    return model.Report(
        exit_status=1,
        tests=(
            model.TestRecord(
                "tests/test_a.py::test_slow",
                "passed",
                312.4,
                ("ABC-1",),
                {"setup": model.Phase("passed", 1.0), "call": model.Phase("passed", 311.4)},
            ),
            model.TestRecord(
                "tests/test_a.py::test_fast",
                "failed",
                12.5,
                (),
                {"call": model.Phase("failed", 12.5)},
            ),
            model.TestRecord("tests/test_b.py::test_skip", "skipped", 0.4, ("ABC-3",)),
        ),
    )


def format_checks(checks: Checks) -> None:
    report = sample_report()
    checks.equal("counts add up", 3, len(report.tests))
    checks.equal("failed counted", 1, report.counts()["failed"])
    checks.equal("skipped counted", 1, report.counts()["skipped"])
    checks.equal("slowest first", "tests/test_a.py::test_slow", report.slowest(1)[0].nodeid)
    checks.equal("gate is strict", 0, len(report.over(312.4)))
    checks.equal("gate catches faster line", 1, len(report.over(100)))
    checks.equal("ticket or dash", "-", report.slowest()[1].ticket)
    checks.equal("slowest phase named", "call", report.slowest(1)[0].slowest_phase())
    checks.equal("no phases means dash", "-", report.tests[2].slowest_phase())

    round_trip = model.Report.from_dict(json.loads(json.dumps(report.as_dict())))
    checks.equal("round trip keeps tickets", ("ABC-1",), round_trip.tests[0].tickets)
    checks.equal("round trip keeps duration", 311.4, round_trip.tests[0].phases["call"].duration_ms)

    checks.raises("format 2 is refused", model.InputError, lambda: model.Report.from_dict(
        {"format": 2, "exit_status": 0, "tests": []}))
    checks.raises("missing nodeid refused", model.InputError, lambda: model.Report.from_dict(
        {"format": 1, "exit_status": 0, "tests": [{"outcome": "passed", "duration_ms": 1}]}))
    checks.raises("unknown outcome refused", model.InputError, lambda: model.Report.from_dict(
        {"format": 1, "exit_status": 0,
         "tests": [{"nodeid": "t", "outcome": "flaky", "duration_ms": 1}]}))
    checks.raises("bool duration refused", model.InputError, lambda: model.Report.from_dict(
        {"format": 1, "exit_status": 0,
         "tests": [{"nodeid": "t", "outcome": "passed", "duration_ms": True}]}))


def file_checks(checks: Checks) -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "report.json"
        model.save(path, sample_report())
        loaded = model.load(path)
        checks.equal("saved and loaded", 3, len(loaded.tests))
        checks.equal("trailing newline", True, path.read_text().endswith("}\n"))

        broken = Path(directory) / "broken.json"
        broken.write_text("{not json")
        checks.raises("broken json refused", model.InputError, lambda: model.load(broken))
        checks.raises(
            "missing file refused", model.InputError, lambda: model.load(Path(directory) / "nope")
        )


def outcome_checks(checks: Checks) -> None:
    passed = model.Phase("passed", 1.0)
    failed = model.Phase("failed", 1.0)
    skipped = model.Phase("skipped", 1.0)
    checks.equal("clean call", "passed", plugin.outcome_of({"call": passed}))
    checks.equal("failed assertion", "failed", plugin.outcome_of({"call": failed}))
    checks.equal(
        "setup failure is an error",
        "error",
        plugin.outcome_of({"setup": failed, "teardown": passed}),
    )
    checks.equal(
        "teardown failure is an error",
        "error",
        plugin.outcome_of({"call": passed, "teardown": failed}),
    )
    checks.equal("skip wins over pass", "skipped", plugin.outcome_of({"setup": skipped}))
    checks.equal(
        "failure beats skip",
        "failed",
        plugin.outcome_of({"setup": skipped, "call": failed}),
    )


def recorder_checks(checks: Checks) -> None:
    recorder = plugin.Recorder()
    recorder.remember_tickets("tests/t.py::test_one", ("ABC-9",))
    recorder.add_phase("tests/t.py::test_one", "setup", model.Phase("passed", 0.5))
    recorder.add_phase("tests/t.py::test_one", "call", model.Phase("passed", 2.0))
    report = recorder.build(0)
    checks.equal("recorder totals phases", 2.5, report.tests[0].duration_ms)
    checks.equal("recorder keeps ticket", "ABC-9", report.tests[0].ticket)
    checks.equal("recorder keeps exit status", 0, report.exit_status)


def main() -> int:
    checks = Checks()
    format_checks(checks)
    file_checks(checks)
    outcome_checks(checks)
    recorder_checks(checks)
    print(f"selftest: {checks.passed} checks passed, {checks.failed} failed")
    return 0 if checks.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
