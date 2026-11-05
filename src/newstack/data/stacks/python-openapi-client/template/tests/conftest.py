from __future__ import annotations

import importlib.util
import threading
from collections.abc import Iterator
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from {{ package_name }}.spec import Spec, load

ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / "fixtures" / "openapi.json"
SERVER_PATH = ROOT / "fixtures" / "server.py"


@pytest.fixture(scope="session")
def spec() -> Spec:
    return load(SPEC_PATH)


def _server_module() -> Any:
    specification = importlib.util.spec_from_file_location("_notes_server_under_test", SERVER_PATH)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _serve(drift: bool) -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _server_module().make_handler(drift))
    thread = threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True
    )
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture(scope="session")
def honest_url() -> Iterator[str]:
    yield from _serve(drift=False)


@pytest.fixture(scope="session")
def drifted_url() -> Iterator[str]:
    yield from _serve(drift=True)
