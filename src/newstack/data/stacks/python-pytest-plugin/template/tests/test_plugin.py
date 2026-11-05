"""The hooks are the product, so these tests run real (nested) pytest sessions.

They use pytester's subprocess mode: the plugin is registered through its
``pytest11`` entry point, and an in-process run would find it already imported.
"""

from pathlib import Path

import pytest

from {{ package_name }} import model as model_mod
from {{ package_name }} import plugin as plugin_mod


def report_of(pytester: pytest.Pytester, path: Path) -> model_mod.Report:
    return model_mod.load(path)


def test_a_report_records_every_phase(pytester: pytest.Pytester, tmp_path: Path) -> None:
    pytester.makepyfile(
        test_sample="""
        import pytest

        @pytest.mark.ticket("ABC-1")
        def test_ok():
            assert True
        """
    )
    path = tmp_path / "report.json"
    result = pytester.runpytest_subprocess("--testmeta-report", str(path))

    result.assert_outcomes(passed=1)
    (test,) = report_of(pytester, path).tests
    assert test.outcome == "passed"
    assert test.ticket == "ABC-1"
    assert set(test.phases) == {"setup", "call", "teardown"}
    assert all(phase.duration_ms >= 0 for phase in test.phases.values())


def test_the_report_is_written_even_when_a_test_fails(
    pytester: pytest.Pytester, tmp_path: Path
) -> None:
    pytester.makepyfile(
        test_bad="""
        import pytest

        @pytest.mark.ticket("ABC-2")
        def test_bad():
            assert 0
        """
    )
    path = tmp_path / "report.json"
    result = pytester.runpytest_subprocess("--testmeta-report", str(path))

    assert result.ret == 1
    report = report_of(pytester, path)
    assert report.exit_status == 1
    assert report.tests[0].outcome == "failed"
    assert report.tests[0].phases["call"].outcome == "failed"


def test_a_teardown_failure_is_an_error_not_a_failure(
    pytester: pytest.Pytester, tmp_path: Path
) -> None:
    pytester.makepyfile(
        test_teardown="""
        import pytest

        @pytest.fixture
        def broken():
            yield
            raise RuntimeError("teardown blew up")

        @pytest.mark.ticket("ABC-3")
        def test_uses(broken):
            assert True
        """
    )
    path = tmp_path / "report.json"
    pytester.runpytest_subprocess("--testmeta-report", str(path))

    assert report_of(pytester, path).tests[0].outcome == "error"


def test_a_skipped_test_is_recorded_as_skipped(pytester: pytest.Pytester, tmp_path: Path) -> None:
    pytester.makepyfile(
        test_skipped="""
        import pytest

        @pytest.mark.ticket("ABC-4")
        @pytest.mark.skip(reason="not yet")
        def test_later():
            assert False
        """
    )
    path = tmp_path / "report.json"
    pytester.runpytest_subprocess("--testmeta-report", str(path))

    assert report_of(pytester, path).tests[0].outcome == "skipped"


def test_strict_mode_refuses_unticketed_tests(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        test_plain="""
        def test_unticketed():
            assert True
        """
    )
    result = pytester.runpytest_subprocess("--testmeta-strict")

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*have no @pytest.mark.ticket marker*", "*test_unticketed*"])


def test_strict_mode_accepts_a_ticketed_suite(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        test_ticketed="""
        import pytest

        @pytest.mark.ticket("ABC-5")
        def test_ok():
            assert True
        """
    )
    result = pytester.runpytest_subprocess("--testmeta-strict")
    result.assert_outcomes(passed=1)


def test_without_the_option_nothing_is_written(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        test_quiet="""
        import pytest

        @pytest.mark.ticket("ABC-6")
        def test_ok():
            assert True
        """
    )
    result = pytester.runpytest_subprocess()
    result.assert_outcomes(passed=1)
    assert not (pytester.path / "report.json").exists()


def test_the_ticket_id_fixture_reads_the_marker(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        test_fixture="""
        import pytest

        @pytest.mark.ticket("ABC-7")
        def test_with_ticket(ticket_id):
            assert ticket_id == "ABC-7"

        def test_without_ticket(ticket_id):
            assert ticket_id == "-"
        """
    )
    result = pytester.runpytest_subprocess()
    result.assert_outcomes(passed=2)


def test_the_marker_survives_strict_markers(pytester: pytest.Pytester) -> None:
    pytester.makeini("[pytest]\naddopts = --strict-markers\n")
    pytester.makepyfile(
        test_marked="""
        import pytest

        @pytest.mark.ticket("ABC-8")
        def test_marked():
            assert True
        """
    )
    result = pytester.runpytest_subprocess()
    result.assert_outcomes(passed=1)


def test_the_header_says_where_the_report_goes(pytester: pytest.Pytester, tmp_path: Path) -> None:
    pytester.makepyfile(
        test_header="""
        import pytest

        @pytest.mark.ticket("ABC-9")
        def test_ok():
            assert True
        """
    )
    path = tmp_path / "report.json"
    result = pytester.runpytest_subprocess("--testmeta-report", str(path))
    result.stdout.fnmatch_lines(["*testmeta: report ->*"])


def test_outcome_of_keeps_failures_and_errors_apart() -> None:
    passed = model_mod.Phase("passed", 1.0)
    failed = model_mod.Phase("failed", 1.0)
    assert plugin_mod.outcome_of({"call": passed}) == "passed"
    assert plugin_mod.outcome_of({"call": failed}) == "failed"
    assert plugin_mod.outcome_of({"setup": failed, "teardown": passed}) == "error"


def test_the_recorder_adds_phases_up() -> None:
    recorder = plugin_mod.Recorder()
    recorder.add_phase("tests/t.py::test_one", "setup", model_mod.Phase("passed", 0.5))
    recorder.add_phase("tests/t.py::test_one", "call", model_mod.Phase("passed", 2.25))

    (test,) = recorder.build(0).tests
    assert test.duration_ms == 2.75
    assert test.ticket == "-"
