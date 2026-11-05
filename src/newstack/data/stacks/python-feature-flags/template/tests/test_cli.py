"""The CLI is what a support engineer uses when the question is "why is it off for me?"."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from {{ package_name }} import cli as subject


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    status = subject.main(list(argv))
    captured = capsys.readouterr()
    return status, captured.out, captured.err


def test_a_full_rollout_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "check", "dark-mode", "--user", "alice")
    assert status == 0
    assert out.startswith("on  inside    dark-mode")


def test_a_kill_switch_exits_one(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "check", "kill-switch-test", "--user", "alice")
    assert status == 1
    assert out.startswith("off off")


def test_a_targeted_user_is_on_without_a_rollout(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "check", "vip-access", "--user", "alice")
    assert status == 0
    assert "targeted" in out
    status, out, _ = run(capsys, "check", "vip-access", "--user", "carol")
    assert status == 1
    assert "outside" in out


def test_the_json_payload_carries_the_arithmetic(capsys: pytest.CaptureFixture[str]) -> None:
    _, out, _ = run(capsys, "check", "new-search", "--user", "alice", "--json")
    payload = json.loads(out)
    assert payload["flag"] == "new-search"
    assert payload["cutoff"] == 5000
    assert payload["variant"] in ("on", "off")
    assert payload["reason"] in ("inside", "outside")


def test_an_unknown_flag_is_not_an_error_but_says_unknown(
    capsys: pytest.CaptureFixture[str],
) -> None:
    status, out, _ = run(capsys, "check", "no-such-flag", "--user", "alice")
    assert status == 1
    assert "unknown" in out


def test_explain_prints_the_rules(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "explain", "checkout-redesign", "--user", "alice")
    assert status in (0, 1)
    assert "salt     checkout-2026-11" in out
    assert "bucket   " in out
    assert "cutoff   1000 (rollout 10%)" in out


def test_list_names_every_flag(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "list")
    assert status == 0
    assert len([line for line in out.splitlines() if line.strip()]) == 5
    assert "kill-switch-test" in out


def test_distribution_measures_a_population(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "distribution", "--users", "2000")
    assert status == 0
    assert "checkout-redesign" in out
    assert "worst deviation" in out


def test_distribution_is_reproducible(capsys: pytest.CaptureFixture[str]) -> None:
    _, first, _ = run(capsys, "distribution", "--users", "500")
    _, second, _ = run(capsys, "distribution", "--users", "500")
    assert first == second


def test_zero_users_is_refused(capsys: pytest.CaptureFixture[str]) -> None:
    status, _, err = run(capsys, "distribution", "--users", "0")
    assert status == 2
    assert "at least 1" in err


def test_a_missing_flags_file_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status, _, err = run(capsys, "--flags", str(tmp_path / "absent.toml"), "list")
    assert status == 2
    assert "cannot read" in err


def test_version_is_available() -> None:
    with pytest.raises(SystemExit) as caught:
        subject.main(["--version"])
    assert caught.value.code == 0
