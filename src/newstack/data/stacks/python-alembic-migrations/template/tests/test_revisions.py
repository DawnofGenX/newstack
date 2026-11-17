"""Tests for migration revision files."""

from __future__ import annotations

from pathlib import Path

from {{ package_name }} import latest_revision


def test_latest_revision() -> None:
    assert latest_revision() == "0002"


def test_revision_files_exist() -> None:
    versions = Path("migrations/versions")
    assert (versions / "0001_create_items.py").is_file()
    assert (versions / "0002_add_status.py").is_file()