from collections.abc import Iterator
from pathlib import Path

import pytest

from {{ package_name }}.store import Store


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    instance = Store(tmp_path / "outbox.db")
    try:
        yield instance
    finally:
        instance.close()
