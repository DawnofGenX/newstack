"""The demo is checked like any other output: a timeline nobody verifies drifts."""

from __future__ import annotations

import pytest

from {{ package_name }} import demo as subject
from {{ package_name }} import model as model_mod


def test_the_default_timeline_is_what_it_claims() -> None:
    timeline = subject.run()
    assert timeline.ok is True
    assert timeline.steps[-1].state is model_mod.State.CLOSED


def test_the_timeline_denies_twice_and_probes_once() -> None:
    timeline = subject.run(failures=3, cooldown=30.0)
    denied = [step for step in timeline.steps if not step.decision.allowed]
    probes = [step for step in timeline.steps if step.decision.reason.endswith("single probe")]
    assert len(denied) == 2
    assert len(probes) == 1
    assert denied[0].decision.reason.startswith("open, next probe in")


def test_the_clock_is_printed_on_every_line() -> None:
    for line in subject.run().lines():
        assert line.startswith("t=")


def test_a_cooldown_of_zero_still_denies_once() -> None:
    timeline = subject.run(failures=1, cooldown=0.0)
    assert timeline.steps[0].state is model_mod.State.CLOSED
    assert any("deny" in line for line in timeline.lines())


@pytest.mark.parametrize("kwargs", [{"failures": 0}, {"successes": 0}])
def test_impossible_scenarios_are_refused(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        subject.run(**kwargs)


def test_a_single_failure_scenario_trips_immediately() -> None:
    timeline = subject.run(failures=1, cooldown=10.0, successes=1)
    assert timeline.ok is True
    assert timeline.steps[2].state is model_mod.State.OPEN
