"""A real server process, so signals and socket teardown are the real thing."""

from __future__ import annotations

import contextlib
import http.client
import socket
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


class Running:
    def __init__(self, drain_timeout: float = 10.0) -> None:
        self.port = free_port()
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "{{ package_name }}",
                "serve",
                "--port",
                str(self.port),
                "--drain-timeout",
                str(drain_timeout),
            ],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines: list[str] = []
        self.reader = threading.Thread(target=self._collect, daemon=True)
        self.reader.start()
        if not self.wait_listening():
            self.stop()
            raise RuntimeError(f"server never listened: {self.output}")

    def _collect(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            self.lines.append(line.rstrip("\n"))

    def wait_listening(self, timeout: float = 10.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with socket.socket() as probe:
                if probe.connect_ex(("127.0.0.1", self.port)) == 0:
                    return True
            if self.process.poll() is not None:
                return False
            time.sleep(0.02)
        return False

    def connection(self, timeout: float = 15.0) -> http.client.HTTPConnection:
        return http.client.HTTPConnection("127.0.0.1", self.port, timeout=timeout)

    def get(self, path: str, timeout: float = 15.0) -> tuple[int, str]:
        connection = self.connection(timeout)
        try:
            connection.request("GET", path)
            response = connection.getresponse()
            return response.status, response.read().decode()
        finally:
            connection.close()

    @property
    def output(self) -> str:
        return "\n".join(self.lines)

    def wait(self, timeout: float = 20.0) -> int:
        code = self.process.wait(timeout=timeout)
        self.reader.join(timeout=2)
        self._close_pipe()
        return code

    def _close_pipe(self) -> None:
        """Closing the pipe matters: an unclosed FileIO surfaces as an unraisable
        exception that pytest turns into an error in whichever test ran next."""
        if self.process.stdout is not None:
            with contextlib.suppress(OSError, ValueError):
                self.process.stdout.close()

    def stop(self) -> None:
        if self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=10)
        self.reader.join(timeout=2)
        self._close_pipe()


class Attempt:
    """One request on its own thread, with the failure kept instead of raised.

    Tests here kill the process mid-response on purpose. A thread that lets the
    resulting reset escape fails whichever test happens to be running when pytest
    collects it, so the error is recorded on the object.
    """

    def __init__(self, server: Running, path: str, timeout: float = 20.0) -> None:
        self.server = server
        self.path = path
        self.timeout = timeout
        self.response: tuple[int, str] | None = None
        self.error: BaseException | None = None
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        try:
            self.response = self.server.get(self.path, self.timeout)
        except (OSError, http.client.HTTPException) as exc:
            self.error = exc

    def start(self) -> Attempt:
        self.thread.start()
        return self

    def join(self, timeout: float = 20.0) -> None:
        self.thread.join(timeout=timeout)


@pytest.fixture()
def running() -> Iterator[Running]:
    server = Running()
    try:
        yield server
    finally:
        server.stop()
