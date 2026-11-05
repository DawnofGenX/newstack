"""The schema table is the single definition of every setting."""

from __future__ import annotations

import pytest

from {{ package_name }} import spec as subject


def test_every_name_is_unique() -> None:
    names = [key.name for key in subject.KEYS]
    assert len(names) == len(set(names))


def test_every_kind_is_known() -> None:
    assert {key.kind for key in subject.KEYS} <= set(subject.KINDS)


def test_a_dotted_name_becomes_a_double_underscore_variable() -> None:
    assert subject.get("server.port").env_name("APP") == "APP_SERVER__PORT"


def test_the_prefix_is_part_of_the_name() -> None:
    assert subject.get("log.level").env_name("SVC") == "SVC_LOG__LEVEL"


def test_an_unknown_setting_lists_the_known_ones() -> None:
    with pytest.raises(subject.ConfigError, match=r"unknown setting 'server\.prot'"):
        subject.get("server.prot")


def test_the_secrets_are_the_two_named_ones() -> None:
    secrets = sorted(key.name for key in subject.KEYS if key.secret)
    assert secrets == ["auth.signing_key", "db.url"]


def test_only_one_setting_is_required() -> None:
    assert [key.name for key in subject.KEYS if key.required] == ["auth.signing_key"]


def test_env_names_covers_the_whole_table() -> None:
    names = subject.env_names("APP")
    assert len(names) == len(subject.KEYS)
    assert names["APP_DB__POOL_SIZE"].name == "db.pool_size"


def test_bounds_are_declared_on_integers() -> None:
    assert subject.get("server.port").maximum == 65535
    assert subject.get("db.pool_size").minimum == 1


def test_a_key_with_a_default_says_so() -> None:
    assert subject.get("features.rate_limit").has_default
    assert not subject.get("auth.signing_key").has_default
