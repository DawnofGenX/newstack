from __future__ import annotations

from {{ package_name }} import demo as subject


def test_every_scenario_is_as_advertised() -> None:
    steps = subject.run()
    assert [step.scenario for step in steps] == [
        "a steady counter",
        "a counter that restarts",
        "a scrape that never happened",
        "the same rollup delivered twice",
    ]
    assert all(step.ok for step in steps)


def test_the_render_says_nothing_was_missed() -> None:
    text = subject.render(subject.run())
    assert "demo: 4 scenarios, 0 not as advertised" in text


def test_a_broken_scenario_is_rendered_as_such() -> None:
    steps = subject.run()
    broken = [subject.Step(scenario="x", lines=["y"], ok=False)]
    assert "NOT as advertised" in subject.render([*steps, *broken])
    assert subject.render(broken).endswith("demo: 1 scenarios, 1 not as advertised")
