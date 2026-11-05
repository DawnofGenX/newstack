from collections.abc import Iterator
from pathlib import Path

import pytest

from {{ package_name }} import schema as schema_mod

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"


@pytest.fixture(autouse=True)
def in_project(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """The CLI defaults point at fixtures/, so run from the project root."""
    monkeypatch.chdir(ROOT)
    yield


@pytest.fixture
def v1() -> dict:
    return schema_mod.load(FIXTURES / "v1.json")


@pytest.fixture
def v2() -> dict:
    return schema_mod.load(FIXTURES / "v2.json")


@pytest.fixture
def v3() -> dict:
    return schema_mod.load(FIXTURES / "v3.json")


@pytest.fixture
def v4() -> dict:
    return schema_mod.load(FIXTURES / "v4.json")
