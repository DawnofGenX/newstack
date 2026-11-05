"""Shared fixtures: a queue in a temporary directory, on a clock we control."""

from __future__ import annotations

import contextlib
import sqlite3
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest

from {{ package_name }} import store as store_module


class Clock:
    """A stand-in for time.time(), so a lease can expire without waiting."""

    def __init__(self, now: float = 1_000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def real_clock() -> Callable[[], float]:
    """For the checks where real elapsed time is the point."""
    return time.time


def _factory(tmp_path: Path, clock: Callable[[], float]) -> Iterator[Callable[..., Any]]:
    opened: list[Any] = []

    def factory(name: str = "queue.db", **kwargs: object) -> Any:
        """Another Store on the same database — what a second process would open."""
        store = store_module.Store(
            tmp_path / name,
            clock=clock,
            backoff_base_s=1.0,
            backoff_cap_s=8.0,
            **kwargs,  # type: ignore[arg-type]
        )
        opened.append(store)
        return store

    yield factory
    for store in opened:
        # A Store belongs to the thread that opened it; a test that opens one in a
        # worker thread must close it there, or the teardown is the error.
        with contextlib.suppress(sqlite3.ProgrammingError):
            store.close()


@pytest.fixture
def make_store(tmp_path: Path, clock: Clock) -> Iterator[Callable[..., Any]]:
    yield from _factory(tmp_path, clock)


@pytest.fixture
def make_real_store(
    tmp_path: Path, real_clock: Callable[[], float]
) -> Iterator[Callable[..., Any]]:
    yield from _factory(tmp_path, real_clock)


@pytest.fixture
def store(make_store: Callable[..., Any]) -> Any:
    return make_store()
