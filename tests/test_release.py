"""Release guards: one version, stated in three places, and a wheel that ships it all."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import newstack

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
CHANGELOG = ROOT / "CHANGELOG.md"
STACKS = ROOT / "src" / "newstack" / "data" / "stacks"

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _pyproject_version() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    found = re.search(r'^version = "([^"]+)"$', text, re.M)
    assert found, "pyproject.toml has no project version"
    return found.group(1)


def _released_entries() -> list[tuple[str, str]]:
    """(version, date) pairs from the CHANGELOG, newest first."""
    text = CHANGELOG.read_text(encoding="utf-8")
    return re.findall(r"^## \[(\d+\.\d+\.\d+)\] - (\d{4}-\d{2}-\d{2})$", text, re.M)


def test_version_is_the_same_in_pyproject_and_the_package() -> None:
    assert _pyproject_version() == newstack.__version__, (
        "pyproject.toml and newstack.__version__ disagree — the wheel would ship one "
        "version while `newstack version` reports another"
    )


def test_version_looks_like_a_release() -> None:
    version = _pyproject_version()
    assert VERSION_RE.match(version), f"not a semver release: {version!r}"
    assert version != "0.0.0"


def test_changelog_head_is_the_version_being_released() -> None:
    entries = _released_entries()
    assert entries, "CHANGELOG.md has no `## [x.y.z] - YYYY-MM-DD` entry"
    assert entries[0][0] == _pyproject_version(), (
        f"CHANGELOG head is {entries[0][0]} but the package is {_pyproject_version()}"
    )


def test_changelog_has_no_unreleased_section_above_the_release() -> None:
    """After a cut, work in progress belongs in a fresh `## [Unreleased]` that is re-added."""
    text = CHANGELOG.read_text(encoding="utf-8")
    head = text.split("## [", 1)[1] if "## [" in text else ""
    assert not head.startswith("[Unreleased]"), (
        "CHANGELOG still has an [Unreleased] section above the release"
    )


def test_changelog_dates_are_real_and_not_in_the_future() -> None:
    today = date.today()
    for version, stamp in _released_entries():
        released = date.fromisoformat(stamp)
        assert released <= today, f"{version} is dated in the future ({stamp})"


def test_changelog_versions_are_unique_and_descending() -> None:
    versions = [version for version, _ in _released_entries()]
    assert len(versions) == len(set(versions)), f"duplicate CHANGELOG entries: {versions}"
    parsed = [tuple(int(part) for part in version.split(".")) for version in versions]
    assert parsed == sorted(parsed, reverse=True), f"CHANGELOG is out of order: {versions}"


def test_every_stack_dir_carries_its_manifest() -> None:
    """The wheel is built from this tree; a stack without stack.json is not shipped."""
    missing = sorted(
        path.name
        for path in STACKS.iterdir()
        if path.is_dir() and not (path / "stack.json").is_file()
    )
    assert not missing, f"stack directories without stack.json: {', '.join(missing)}"
