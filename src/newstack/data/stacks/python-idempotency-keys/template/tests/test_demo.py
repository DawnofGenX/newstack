from {{ package_name }} import demo as demo_mod


def test_the_demo_runs_four_scenarios(tmp_path) -> None:
    steps = demo_mod.run(tmp_path / "demo")
    assert len(steps) == 4
    assert all(step.ok for step in steps)


def test_the_demo_names_the_effect_count(tmp_path) -> None:
    rendered = demo_mod.render(demo_mod.run(tmp_path / "demo"))
    assert "the provider was called 1 time(s) for 1200 minor units" in rendered
    assert "demo: 4 scenarios, 0 not as advertised" in rendered


def test_the_crash_scenario_shows_a_second_charge(tmp_path) -> None:
    steps = {step.scenario: step for step in demo_mod.run(tmp_path / "demo")}
    crash = steps["a crash between the effect and the row"]
    assert "called 2 time(s)" in " ".join(crash.lines)
    assert "nothing in the key table can undo an effect" in " ".join(crash.lines)


def test_the_concurrent_scenario_charges_once(tmp_path) -> None:
    steps = {step.scenario: step for step in demo_mod.run(tmp_path / "demo")}
    concurrent = steps["two workers, one key"]
    assert concurrent.ok is True
    assert "called 1 time(s)" in " ".join(concurrent.lines)


def test_the_payload_is_json_shaped(tmp_path) -> None:
    payload = demo_mod.payload(demo_mod.run(tmp_path / "demo"))
    assert payload["missed"] == 0
    assert len(payload["scenarios"]) == 4
    assert isinstance(payload["scenarios"][0]["lines"], list)
