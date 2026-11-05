"""Fixtures: a temporary database, so no test can see another's rows."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from {{ package_name }}.store import Store


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    with Store(tmp_path / "items.db") as opened:
        yield opened
