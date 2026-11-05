"""Signals are delivered to a real process; nothing here is simulated."""

from __future__ import annotations

import signal
import socket
import time

from conftest import Attempt, Running

DONE = "done\n"


def test_a_sigterm_with_nothing_in_flight_exits_zero(running: Running) -> None:
    assert running.get("/health") == (200, "ok\n")
    running.process.send_signal(signal.SIGTERM)

    assert running.wait() == 0
    assert "signal 15: draining 0 request(s)" in running.output
    assert "drained 0 request(s)" in running.output
    assert running.output.rstrip().endswith("stopped")


def test_an_in_flight_request_finishes_before_the_process_does(running: Running) -> None:
    worker = Attempt(running, "/work?ms=800").start()
    time.sleep(0.2)
    running.process.send_signal(signal.SIGTERM)

    assert running.wait() == 0
    worker.join()
    assert worker.error is None
    assert worker.response == (200, DONE)
    assert "draining 1 request(s)" in running.output
    assert "drained 1 request(s)" in running.output


def test_the_listener_stops_accepting_while_the_drain_runs(running: Running) -> None:
    worker = Attempt(running, "/work?ms=1200").start()
    time.sleep(0.2)
    running.process.send_signal(signal.SIGTERM)

    # A bare socket: what matters is whether the kernel still has a listener for this
    # port. An HTTP client would instead prove that the keep-alive path answers 503.
    deadline = time.monotonic() + 5.0
    refused = False
    while time.monotonic() < deadline:
        with socket.socket() as probe:
            probe.settimeout(0.5)
            code = probe.connect_ex(("127.0.0.1", running.port))
        if code != 0:
            refused = True
            break
        time.sleep(0.05)

    assert refused, "the listening socket was still accepting after the drain began"
    assert running.process.poll() is None, "the process exited before its request finished"
    worker.join()
    assert running.wait() == 0
    assert "drained 1 request(s)" in running.output


def test_a_keep_alive_connection_gets_a_503_after_the_drain_begins(running: Running) -> None:
    connection = running.connection()
    try:
        connection.request("GET", "/health")
        assert connection.getresponse().read() == b"ok\n"
        running.process.send_signal(signal.SIGTERM)
        time.sleep(0.3)
        connection.request("GET", "/health")
        response = connection.getresponse()
        assert response.status == 503
        assert response.read() == b"draining\n"
        assert response.getheader("Connection") == "close"
    finally:
        connection.close()
    assert running.wait() == 0


def test_a_second_signal_forces_the_exit() -> None:
    server = Running(drain_timeout=30.0)
    try:
        worker = Attempt(server, "/work?ms=5000").start()
        time.sleep(0.2)
        server.process.send_signal(signal.SIGTERM)
        time.sleep(0.3)
        server.process.send_signal(signal.SIGTERM)

        assert server.wait(timeout=10) == 130
        assert "forcing exit" in server.output
        worker.join()
        assert worker.error is not None
    finally:
        server.stop()


def test_a_request_that_outlives_the_deadline_exits_one() -> None:
    server = Running(drain_timeout=0.3)
    try:
        worker = Attempt(server, "/work?ms=5000").start()
        time.sleep(0.2)
        server.process.send_signal(signal.SIGTERM)

        assert server.wait(timeout=10) == 1
        assert "drain timeout after 0.3s" in server.output
        assert "1 request(s) unfinished" in server.output
        worker.join()
        assert worker.error is not None
    finally:
        server.stop()


def test_sigint_is_treated_like_sigterm(running: Running) -> None:
    running.process.send_signal(signal.SIGINT)
    assert running.wait() == 0
    assert "signal 2: draining" in running.output
