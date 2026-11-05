from pathlib import Path

from {{ package_name }} import demo as demo_mod


def test_the_demo_proves_three_things(tmp_path: Path) -> None:
    steps = demo_mod.run(tmp_path / "demo")
    assert [step.verdict for step in steps] == ["lost", "exactly once", "in order"]
    assert all(step.ok for step in steps)


def test_the_dual_write_step_really_has_no_event(tmp_path: Path) -> None:
    step = demo_mod.run(tmp_path / "demo")[0]
    assert any("outbox rows carrying the event: 0" in line for line in step.lines)


def test_the_last_line_counts_the_misses(tmp_path: Path) -> None:
    lines = demo_mod.lines(demo_mod.run(tmp_path / "demo"))
    assert lines[-1] == "demo: 3 scenarios, 0 not as advertised"
    assert lines[0].startswith("the write without an outbox")
