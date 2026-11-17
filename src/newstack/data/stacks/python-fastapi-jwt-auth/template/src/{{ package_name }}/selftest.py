"""Offline self-test: import app and hit /health via TestClient."""

from __future__ import annotations

from fastapi.testclient import TestClient

from .main import create_app


def run() -> int:
    app = create_app()
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200, r.text
        assert r.json() == {"status": "ok"}, r.json()
    print("selftest: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())