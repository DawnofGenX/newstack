"""Shared fixtures: every test builds its own environment mapping."""

from __future__ import annotations

import textwrap
from collections.abc import Callable
from pathlib import Path

import pytest


@pytest.fixture
def write_config(tmp_path: Path) -> Callable[[str], Path]:
    def write(body: str) -> Path:
        path = tmp_path / "config.toml"
        path.write_text(textwrap.dedent(body).lstrip())
        return path

    return write


@pytest.fixture
def signed() -> dict[str, str]:
    return {"APP_AUTH__SIGNING_KEY": "s3cret"}
