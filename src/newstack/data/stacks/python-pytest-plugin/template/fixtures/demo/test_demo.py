"""A project that uses the plugin, not a test of it."""

import pytest


@pytest.mark.ticket("DEMO-1")
def test_addition() -> None:
    assert 2 + 2 == 4


@pytest.mark.ticket("DEMO-2")
@pytest.mark.skip(reason="kept as an example of a skip")
def test_skipped() -> None:
    assert 2 + 2 == 5
