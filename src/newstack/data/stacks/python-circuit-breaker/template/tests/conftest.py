"""Shared fixtures: a clock the tests move, and a breaker built on it."""

from __future__ import annotations

from typing import Any

import pytest

from {{ package_name }} import breaker as breaker_mod
from {{ package_name }} import clock as clock_mod


@pytest.fixture
def clock() -> clock_mod.FakeClock:
    return clock_mod.FakeClock()


@pytest.fixture
def make_breaker(clock: clock_mod.FakeClock):
    def factory(**kwargs: Any) -> breaker_mod.Breaker:
        return breaker_mod.Breaker(clock=clock, **kwargs)

    return factory
