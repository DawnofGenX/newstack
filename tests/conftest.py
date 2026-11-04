"""Test isolation.

Two environment variables can quietly change what the registry sees:
``NEWSTACK_STACKS`` (extra stack directories) and ``NEWSTACK_HOME`` (installed
stacks). They are pinned *at import time*, before pytest collects test modules —
parametrisation such as ``tests/test_stacks.py`` runs during collection, so a
function-scoped fixture would come too late and a developer's local install would
show up as a stack with no template tracked by this repository.

The fixture then re-pins them per test, so one test cannot see another's install.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_PINNED_HOME = Path(tempfile.mkdtemp(prefix="newstack-tests-home-"))
os.environ["NEWSTACK_HOME"] = str(_PINNED_HOME)
os.environ.pop("NEWSTACK_STACKS", None)


@pytest.fixture(autouse=True)
def isolated_registry(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWSTACK_HOME", str(tmp_path / "newstack-home"))
    monkeypatch.delenv("NEWSTACK_STACKS", raising=False)
    return tmp_path / "newstack-home"
