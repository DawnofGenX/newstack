"""The state machine, with no sockets and no signals involved."""

from __future__ import annotations

import threading
import time

import pytest

from {{ package_name }}.lifecycle import Lifecycle, Phase


def test_a_fresh_lifecycle_is_running() -> None:
    machine = Lifecycle()
    assert machine.phase is Phase.RUNNING
    assert machine.in_flight == 0
    assert machine.admit()


def test_the_drain_starts_once() -> None:
    machine = Lifecycle()
    assert machine.begin_drain()
    assert not machine.begin_drain()
    assert machine.phase is Phase.DRAINING


def test_new_requests_are_refused_during_a_drain() -> None:
    machine = Lifecycle()
    machine.begin_drain()
    assert not machine.admit()
    assert machine.in_flight == 0


def test_admitted_requests_are_counted_until_released() -> None:
    machine = Lifecycle()
    assert machine.admit() and machine.admit()
    assert machine.in_flight == 2
    machine.release()
    assert machine.in_flight == 1
    machine.release()
    assert machine.in_flight == 0
    assert machine.served == 2


def test_idle_waits_for_the_last_release() -> None:
    machine = Lifecycle(2.0)
    machine.admit()
    machine.begin_drain()
    assert not machine.wait_for_idle(0.05)
    releaser = threading.Timer(0.05, machine.release)
    releaser.start()
    assert machine.wait_for_idle(2.0)
    releaser.join()
    assert machine.phase is Phase.STOPPED
    assert machine.drain_ok


def test_a_hung_request_times_out_and_is_not_success() -> None:
    machine = Lifecycle(0.05)
    machine.admit()
    machine.begin_drain()
    started = time.monotonic()
    assert not machine.wait_for_idle()
    assert time.monotonic() - started >= 0.04
    assert not machine.drain_ok
    assert machine.phase is not Phase.STOPPED


@pytest.mark.parametrize("timeout", [0.0, -1.0])
def test_a_meaningless_timeout_is_refused(timeout: float) -> None:
    with pytest.raises(ValueError):
        Lifecycle(timeout)
