"""Each layer is read into raw values plus the problems it found on its own."""

from __future__ import annotations

from pathlib import Path

import pytest

from {{ package_name }} import sources as subject
from {{ package_name }} import spec as spec_mod
from {{ package_name }}.spec import ConfigError


def parse(name: str, raw: object, where: str = "env TEST") -> object:
    return subject.parse(spec_mod.get(name), raw, where)


def test_integer_accepts_text_and_int() -> None:
    assert parse("server.port", "9100") == 9100
    assert parse("server.port", 9100) == 9100


def test_integer_refuses_underscores_with_a_hint() -> None:
    with pytest.raises(ConfigError, match="not numbers anyone types"):
        parse("server.port", "1_000")


def test_integer_refuses_a_boolean() -> None:
    with pytest.raises(ConfigError, match="expected an integer, got a boolean"):
        parse("server.port", True)


@pytest.mark.parametrize("text", ["true", "TRUE", "yes", "on", "1"])
def test_true_words(text: str) -> None:
    assert parse("features.rate_limit", text) is True


@pytest.mark.parametrize("text", ["false", "No", "off", "0"])
def test_false_words(text: str) -> None:
    assert parse("features.rate_limit", text) is False


def test_boolean_is_not_int() -> None:
    with pytest.raises(ConfigError, match="expected a boolean"):
        parse("features.rate_limit", "2")


@pytest.mark.parametrize(("text", "milliseconds"), [("250ms", 250), ("5s", 5000), ("2m", 120000)])
def test_durations(text: str, milliseconds: int) -> None:
    assert parse("server.timeout", text) == milliseconds


def test_a_duration_needs_a_unit() -> None:
    with pytest.raises(ConfigError, match="expected a duration"):
        parse("server.timeout", "5")


def test_list_from_comma_text() -> None:
    assert parse("features.allowed_origins", "a, b") == ("a", "b")


def test_empty_list_text_is_an_empty_tuple() -> None:
    assert parse("features.allowed_origins", "") == ()


def test_list_with_a_hole_is_refused() -> None:
    with pytest.raises(ConfigError, match="empty item"):
        parse("features.allowed_origins", "a,,b")


def test_choice_is_lowercased() -> None:
    assert parse("log.level", "WARNING") == "warning"


def test_choice_outside_the_set() -> None:
    with pytest.raises(ConfigError, match="expected one of debug"):
        parse("log.level", "verbose")


def test_bounds_are_checked_after_parsing() -> None:
    with pytest.raises(ConfigError, match="below the minimum"):
        parse("db.pool_size", "0")
    with pytest.raises(ConfigError, match="above the maximum"):
        parse("server.port", "70000")


def test_the_error_names_the_origin() -> None:
    with pytest.raises(ConfigError, match=r"file notes.toml:1"):
        parse("server.port", "abc", "file notes.toml:1")


def test_file_layer_reads_and_flattens(write_config) -> None:
    path = write_config(
        """
        [server]
        port = 9100

        [db]
        pool_size = 12
        """
    )
    layer, problems = subject.from_file(path)
    assert problems == []
    assert layer["server.port"] == (9100, f"file {path}")
    assert layer["db.pool_size"][0] == 12


def test_an_unknown_file_key_is_a_typo(write_config) -> None:
    path = write_config(
        """
        [server]
        tymeout = "9s"
        """
    )
    _, problems = subject.from_file(path)
    assert len(problems) == 1
    assert "tymeout" in problems[0]
    assert "no setting answers to that name" in problems[0]


def test_a_broken_file_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "broken.toml"
    path.write_text("[server\nport = 1\n")
    with pytest.raises(ConfigError, match="is not valid TOML"):
        subject.from_file(path)


def test_a_missing_file_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="cannot read"):
        subject.load_file(tmp_path / "nope.toml")


def test_env_layer_keeps_its_variable_name() -> None:
    layer, problems = subject.from_env({"APP_SERVER__PORT": "9200"}, "APP")
    assert problems == []
    assert layer["server.port"] == ("9200", "env APP_SERVER__PORT")


def test_env_layer_ignores_other_prefixes() -> None:
    layer, problems = subject.from_env({"HOME": "/root", "OTHER_AUTH__SIGNING_KEY": "x"}, "APP")
    assert layer == {}
    assert problems == []


def test_env_layer_flags_a_single_underscore() -> None:
    _, problems = subject.from_env({"APP_SERVER_PORT": "9200"}, "APP")
    assert len(problems) == 1
    assert "double underscore" in problems[0]


def test_flag_layer_parses_key_value() -> None:
    layer, problems = subject.from_flags(["log.level=debug", "log.level=warning"])
    assert problems == []
    assert layer["log.level"][0] == "warning"


def test_flag_layer_reports_malformed_and_unknown() -> None:
    _, problems = subject.from_flags(["novalue", "nope.key=1", "=1"])
    assert len(problems) == 3
    assert any("expected key=value" in problem for problem in problems)


def test_a_value_equals_sign_is_kept() -> None:
    layer, problems = subject.from_flags(["db.url=postgres://u:p@h/db"])
    assert problems == []
    assert layer["db.url"][0] == "postgres://u:p@h/db"
