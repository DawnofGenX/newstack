"""The exit codes are the contract the shell depends on."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from {{ package_name }} import cli as subject


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("APP_SERVER__PORT", "APP_LOG__LEVEL", "APP_DB__URL", "APP_AUTH__SIGNING_KEY"):
        monkeypatch.delenv(name, raising=False)


def test_a_missing_required_key_is_exit_two(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["check"]) == subject.EXIT_UNUSABLE
    assert "auth.signing_key is required" in capsys.readouterr().err


def test_a_complete_configuration_is_exit_zero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("APP_AUTH__SIGNING_KEY", "s3cret")
    assert subject.main(["check"]) == subject.EXIT_OK
    out = capsys.readouterr().out
    assert "check  ok: 10 settings" in out
    assert "1 from a layer" in out


def test_strict_gates_a_secret_that_ships_with_the_code(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("APP_AUTH__SIGNING_KEY", "s3cret")
    assert subject.main(["check", "--strict"]) == subject.EXIT_DEFAULT_SECRET
    assert "db.url is still the schema default" in capsys.readouterr().err


def test_strict_passes_once_every_secret_is_supplied(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("APP_AUTH__SIGNING_KEY", "s3cret")
    monkeypatch.setenv("APP_DB__URL", "postgres://localhost/app")
    assert subject.main(["check", "--strict"]) == subject.EXIT_OK
    assert "gate   no secret is at its default" in capsys.readouterr().out


def test_show_prints_value_and_source(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("APP_AUTH__SIGNING_KEY", "s3cret")
    monkeypatch.setenv("APP_LOG__LEVEL", "debug")
    assert subject.main(["show"]) == subject.EXIT_OK
    out = capsys.readouterr().out
    assert "log.level" in out
    assert "debug" in out
    assert "env" in out


def test_show_hides_a_secret(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("APP_AUTH__SIGNING_KEY", "s3cret")
    subject.main(["show"])
    out = capsys.readouterr().out
    assert "s3cret" not in out
    assert "***" in out


def test_show_reveal_prints_the_secret(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("APP_AUTH__SIGNING_KEY", "s3cret")
    subject.main(["show", "--reveal"])
    assert "s3cret" in capsys.readouterr().out


def test_show_changed_lists_only_the_layers(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("APP_AUTH__SIGNING_KEY", "s3cret")
    subject.main(["show", "--changed"])
    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert len(lines) == 1
    assert lines[0].startswith("auth.signing_key")


def test_show_json_is_machine_readable(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("APP_AUTH__SIGNING_KEY", "s3cret")
    assert subject.main(["show", "--json"]) == subject.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["values"]["auth.signing_key"]["value"] == "***"
    assert payload["values"]["server.port"]["source"] == "default"


def test_get_refuses_a_secret(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("APP_AUTH__SIGNING_KEY", "s3cret")
    assert subject.main(["get", "auth.signing_key"]) == subject.EXIT_UNUSABLE
    assert "is a secret" in capsys.readouterr().err


def test_get_reveal_prints_it(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("APP_AUTH__SIGNING_KEY", "s3cret")
    assert subject.main(["get", "auth.signing_key", "--reveal"]) == subject.EXIT_OK
    assert capsys.readouterr().out.strip() == "s3cret"


def test_get_prints_a_computed_duration(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("APP_AUTH__SIGNING_KEY", "s3cret")
    monkeypatch.setenv("APP_SERVER__TIMEOUT", "1500ms")
    assert subject.main(["get", "server.timeout"]) == subject.EXIT_OK
    assert capsys.readouterr().out.strip() == "1500"


def test_an_unknown_setting_is_exit_two(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("APP_AUTH__SIGNING_KEY", "s3cret")
    assert subject.main(["get", "server.prot"]) == subject.EXIT_UNUSABLE
    assert "unknown setting" in capsys.readouterr().err


def test_a_broken_file_is_exit_two(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("APP_AUTH__SIGNING_KEY", "s3cret")
    path = tmp_path / "broken.toml"
    path.write_text("[log]\nlevel = 'verbose'\n")
    assert subject.main(["check", "--config", str(path)]) == subject.EXIT_UNUSABLE
    assert "expected one of" in capsys.readouterr().err


def test_a_flag_overrides_the_environment(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("APP_AUTH__SIGNING_KEY", "s3cret")
    monkeypatch.setenv("APP_LOG__LEVEL", "debug")
    assert subject.main(["get", "log.level", "--set", "log.level=error"]) == subject.EXIT_OK
    assert capsys.readouterr().out.strip() == "error"


def test_the_version_flag_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        subject.main(["--version"])
    assert caught.value.code == 0
    assert subject.PROGRAM in capsys.readouterr().out


def test_a_missing_subcommand_is_exit_two() -> None:
    with pytest.raises(SystemExit) as caught:
        subject.main([])
    assert caught.value.code == 2


def test_selftest_runs_from_the_cli(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["selftest"]) == 0
    assert "0 failed" in capsys.readouterr().out
