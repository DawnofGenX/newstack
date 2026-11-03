"""Route tests for {{ title }}."""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app


@pytest.fixture()
def app() -> Flask:
    """Build a fresh application per test so no state leaks between tests."""
    return create_app()


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    return app.test_client()


def test_health(client: FlaskClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_items_starts_empty(client: FlaskClient) -> None:
    response = client.get("/items")

    assert response.status_code == 200
    assert response.get_json() == []
