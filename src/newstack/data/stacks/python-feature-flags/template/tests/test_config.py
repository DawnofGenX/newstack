"""The flags file: one place for typos to be caught, with every mistake named."""

from __future__ import annotations

from pathlib import Path

import pytest

from {{ package_name }} import config as subject
from {{ package_name }} import model


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "flags.toml"
    path.write_text(text)
    return path


def test_a_minimal_file_loads(tmp_path: Path) -> None:
    flags = subject.load(write(tmp_path, '[[flag]]\nname = "a"\nrollout = 5\nsalt = "s"\n'))
    assert flags["a"].rollout == 5


def test_the_shipped_fixture_loads_and_has_targets(tmp_path: Path) -> None:
    flags = subject.load(Path("fixtures/flags.toml"))
    assert len(flags) == 5
    assert flags["vip-access"].targets == frozenset({"alice", "bob"})
    assert flags["kill-switch-test"].enabled is False


def test_a_typo_is_named_with_the_known_keys(tmp_path: Path) -> None:
    text = '[[flag]]\nname = "a"\nrollout = 5\nsalt = "s"\nrolout = 6\n'
    with pytest.raises(model.InputError, match="unknown key"):
        subject.load(write(tmp_path, text))


@pytest.mark.parametrize("targets", ['"alice"', "5", "[1, 2]"])
def test_targets_must_be_a_list_of_strings(tmp_path: Path, targets: str) -> None:
    text = f'[[flag]]\nname = "a"\nsalt = "s"\ntargets = {targets}\n'
    with pytest.raises(model.InputError, match="targets must be a list"):
        subject.load(write(tmp_path, text))


def test_a_duplicate_flag_is_refused(tmp_path: Path) -> None:
    text = '[[flag]]\nname = "a"\nsalt = "s"\n\n[[flag]]\nname = "a"\nsalt = "t"\n'
    with pytest.raises(model.InputError, match="duplicate flag"):
        subject.load(write(tmp_path, text))


def test_broken_toml_is_refused_with_the_file_name(tmp_path: Path) -> None:
    with pytest.raises(model.InputError, match="is not valid TOML"):
        subject.load(write(tmp_path, "this is not toml"))


def test_a_missing_file_is_refused(tmp_path: Path) -> None:
    with pytest.raises(model.InputError, match="cannot read"):
        subject.load(tmp_path / "absent.toml")


def test_two_bad_flags_are_both_reported(tmp_path: Path) -> None:
    text = (
        '[[flag]]\nname = "a"\nrollout = 200\nsalt = "s"\n\n'
        '[[flag]]\nname = "b"\nsalt = "s"\nenabled = "yes"\n'
    )
    with pytest.raises(model.InputError) as caught:
        subject.load(write(tmp_path, text))
    message = str(caught.value)
    assert "flag a: rollout must be between 0 and 100" in message
    assert "flag b: enabled must be true or false" in message
