"""Check the shutdown, including a real SIGTERM delivered to this process."""

from __future__ import annotations

import os
import signal
import socket
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable

from .lifecycle import Lifecycle, Phase
from .service import serve


class Checks:
    def __init__(self) -> None:
        self.passed = 0
        self.failed: list[str] = []

    def ok(self, label: str, condition: bool, detail: str = "") -> None:
        if condition:
            self.passed += 1
            print(f"ok     {label}")
        else:
            self.failed.append(label)
            print(f"FAIL   {label}{': ' + detail if detail else ''}")

    def equal(self, label: str, actual: object, expected: object) -> None:
        self.ok(label, actual == expected, f"expected {expected!r}, got {actual!r}")

    def raises(self, label: str, error: type[Exception], call: Callable[[], object]) -> None:
        try:
            call()
        except error:
            self.ok(label, True)
        except Exception as caught:
            self.ok(label, False, f"raised {type(caught).__name__}: {caught}")
        else:
            self.ok(label, False, "nothing was raised")


def _lifecycle_checks(checks: Checks) -> None:
    machine = Lifecycle(1.0)
    checks.equal("a new lifecycle is running", machine.phase, Phase.RUNNING)
    checks.ok("a running lifecycle admits work", machine.admit())
    checks.equal("admitted work is counted", machine.in_flight, 1)
    checks.ok("the first drain wins", machine.begin_drain())
    checks.ok("a second drain is a no-op", not machine.begin_drain())
    checks.ok("a draining lifecycle refuses new work", not machine.admit())
    checks.ok("it is not idle while a request runs", not machine.wait_for_idle(0.05))
    checks.ok("a refused request leaves the count alone", machine.in_flight == 1)
    machine.release()
    checks.ok("it is idle once the last request ends", machine.wait_for_idle(1.0))
    checks.equal("idle means stopped", machine.phase, Phase.STOPPED)
    checks.ok("the outcome is recorded", machine.drain_ok)
    checks.equal("served requests are counted", machine.served, 1)
    checks.raises("a zero timeout is refused", ValueError, lambda: Lifecycle(0))

    stuck = Lifecycle(0.05)
    stuck.admit()
    stuck.begin_drain()
    checks.ok("a request that never ends times out", not stuck.wait_for_idle())
    checks.ok("a timeout is not success", not stuck.drain_ok)


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _wait_until_listening(port: int, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.02)
    return False


def _signal_checks(checks: Checks) -> None:
    port = _free_port()
    result: dict[str, object] = {}
    done = threading.Event()

    def client() -> None:
        try:
            if not _wait_until_listening(port):
                result["error"] = "the server never listened"
                return
            response = urllib.request.urlopen(
                f"http://127.0.0.1:{port}/work?ms=400", timeout=10
            )
            try:
                result["body"] = response.read().decode()
                result["status"] = response.status
            finally:
                response.close()
        except (urllib.error.URLError, OSError) as error:
            result["error"] = repr(error)
        finally:
            done.set()

    def signaller() -> None:
        if not _wait_until_listening(port):
            result["error"] = "the server never listened"
            done.set()
            return
        worker = threading.Thread(target=client)
        worker.start()
        time.sleep(0.15)
        os.kill(os.getpid(), signal.SIGTERM)
        worker.join()

    thread = threading.Thread(target=signaller)
    thread.start()
    code = serve(port=port, drain_timeout=5.0)
    thread.join(timeout=10)
    done.wait(timeout=10)

    checks.equal("a SIGTERM exits cleanly", code, 0)
    checks.equal("the in-flight request finished", result.get("status"), 200)
    checks.equal("and received its body", result.get("body"), "done\n")
    checks.ok("no client error", "error" not in result, str(result.get("error")))

    ready = _free_port()
    stop = threading.Event()

    def drain_anyway() -> None:
        if _wait_until_listening(ready):
            os.kill(os.getpid(), signal.SIGTERM)
        stop.set()

    thread = threading.Thread(target=drain_anyway)
    thread.start()
    checks.equal("a SIGTERM with nothing in flight also exits 0", serve(port=ready), 0)
    thread.join(timeout=10)


def run_selftest() -> bool:
    checks = Checks()
    _lifecycle_checks(checks)
    _signal_checks(checks)
    total = checks.passed + len(checks.failed)
    if checks.failed:
        print(f"selftest: {len(checks.failed)} of {total} checks failed")
        return False
    print(f"selftest: {checks.passed} checks passed")
    return True
