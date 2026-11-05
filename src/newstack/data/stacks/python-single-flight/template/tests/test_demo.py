from __future__ import annotations

from {{ package_name }} import demo as subject


def test_four_scenarios_all_hold() -> None:
    steps = subject.run()
    assert [step.scenario for step in steps] == [
        "thirty callers, one slow loader",
        "a slow key does not block another",
        "a failed load is remembered for nobody",
        "a TTL starts when the value became readable",
    ]
    assert all(step.ok for step in steps)


def test_the_footer_counts_misses() -> None:
    assert "demo: 4 scenarios, 0 not as advertised" in subject.render(subject.run())
    broken = [subject.Step(scenario="x", lines=["y"], ok=False)]
    assert "NOT as advertised" in subject.render(broken)


def test_an_error_line_names_the_key() -> None:
    failure = demo_flight_error()
    assert subject.error_of(failure).startswith("k: ConnectionError: down")


def demo_flight_error() -> subject.FlightError:
    return subject.FlightError("k", ConnectionError("down"))
