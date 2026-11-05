"""The merge order and the provenance are the product here."""

from __future__ import annotations

import pytest

from {{ package_name }} import resolve as subject
from {{ package_name }}.spec import ConfigError


def test_the_layers_are_declared_in_order() -> None:
    assert subject.LAYER_ORDER == ("file", "env", "flag")


def test_an_empty_environment_reports_the_required_key() -> None:
    resolution = subject.resolve(environ={})
    assert not resolution.ok
    assert any("auth.signing_key is required" in problem for problem in resolution.problems)


def test_everything_else_survives_a_missing_required_key(signed: dict[str, str]) -> None:
    resolution = subject.resolve(environ=signed)
    assert resolution.ok
    assert len(resolution.values) == 10


def test_defaults_are_marked_as_such(signed: dict[str, str]) -> None:
    resolution = subject.resolve(environ=signed)
    value = resolution.get("server.port")
    assert value.value == 8000
    assert value.source == "default"
    assert value.origin == "default"


def test_env_beats_the_default(signed: dict[str, str]) -> None:
    resolution = subject.resolve(environ={**signed, "APP_SERVER__PORT": "9200"})
    assert resolution.get("server.port").value == 9200
    assert resolution.get("server.port").source == "env"


def test_file_beats_the_default(write_config, signed: dict[str, str]) -> None:
    config = write_config(
        """
        [server]
        port = 9100
        """
    )
    resolution = subject.resolve(config=config, environ=signed)
    assert resolution.get("server.port").value == 9100
    assert resolution.get("server.port").source == "file"


def test_env_beats_the_file(write_config, signed: dict[str, str]) -> None:
    config = write_config(
        """
        [server]
        port = 9100
        """
    )
    resolution = subject.resolve(
        config=config, environ={**signed, "APP_SERVER__PORT": "9200"}
    )
    assert resolution.get("server.port").value == 9200
    assert resolution.get("server.port").source == "env"


def test_flags_beat_everything(write_config, signed: dict[str, str]) -> None:
    config = write_config(
        """
        [server]
        port = 9100

        [log]
        level = "warning"
        """
    )
    resolution = subject.resolve(
        config=config,
        environ={**signed, "APP_SERVER__PORT": "9200"},
        flags=["server.port=9300"],
    )
    assert resolution.get("server.port").value == 9300
    assert resolution.get("server.port").source == "flag"
    assert resolution.get("log.level").source == "file"


def test_the_origin_says_where_it_came_from(signed: dict[str, str]) -> None:
    resolution = subject.resolve(environ={**signed, "APP_LOG__LEVEL": "debug"})
    assert resolution.get("log.level").origin == "env APP_LOG__LEVEL"


def test_changed_lists_only_the_layers(signed: dict[str, str]) -> None:
    resolution = subject.resolve(environ={**signed, "APP_LOG__LEVEL": "debug"})
    assert [value.key.name for value in resolution.changed()] == [
        "auth.signing_key",
        "log.level",
    ]


def test_a_secret_is_masked_until_asked(signed: dict[str, str]) -> None:
    value = subject.resolve(environ=signed).get("auth.signing_key")
    assert value.shown() == "***"
    assert value.shown(True) == "s3cret"


def test_a_plain_setting_is_never_masked(signed: dict[str, str]) -> None:
    assert subject.resolve(environ=signed).get("server.host").shown() == "127.0.0.1"


def test_a_shipped_secret_default_is_listed(signed: dict[str, str]) -> None:
    names = [value.key.name for value in subject.resolve(environ=signed).default_secrets()]
    assert names == ["db.url"]


def test_an_overridden_secret_is_not_listed(signed: dict[str, str]) -> None:
    resolution = subject.resolve(environ={**signed, "APP_DB__URL": "postgres://x/y"})
    assert resolution.default_secrets() == []


def test_an_unresolved_key_says_so() -> None:
    with pytest.raises(ConfigError, match="did not resolve"):
        subject.resolve(environ={}).get("auth.signing_key")


def test_every_problem_is_collected_in_one_pass(write_config) -> None:
    config = write_config(
        """
        [server]
        port = 70000
        tymeout = "9s"

        [log]
        level = "verbose"
        """
    )
    resolution = subject.resolve(config=config, environ={})
    assert len(resolution.problems) >= 4
    assert any("above the maximum" in problem for problem in resolution.problems)
    assert any("tymeout" in problem for problem in resolution.problems)
    assert any("verbose" in problem for problem in resolution.problems)


def test_a_bad_value_does_not_hide_the_good_ones(write_config, signed: dict[str, str]) -> None:
    config = write_config(
        """
        [server]
        port = 70000

        [db]
        pool_size = 9
        """
    )
    resolution = subject.resolve(config=config, environ=signed)
    assert not resolution.ok
    assert resolution.get("db.pool_size").value == 9


def test_durations_arrive_in_milliseconds(signed: dict[str, str]) -> None:
    resolution = subject.resolve(environ={**signed, "APP_SERVER__TIMEOUT": "1500ms"})
    assert resolution.get("server.timeout").value == 1500
