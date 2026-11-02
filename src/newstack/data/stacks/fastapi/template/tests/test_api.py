from fastapi.testclient import TestClient

from {{ package_name }}.main import create_app


def client() -> TestClient:
    return TestClient(create_app())


def test_health() -> None:
    response = client().get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_items_start_empty() -> None:
    assert client().get("/items").json() == []


def test_create_then_fetch_item() -> None:
    api = client()
    created = api.post("/items", json={"name": "pen", "price": 1.5})
    assert created.status_code == 201
    body = created.json()
    assert body["id"] == 1
    assert body["name"] == "pen"

    fetched = api.get(f"/items/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == body
    assert api.get("/items").json() == [body]


def test_unknown_item_is_404() -> None:
    assert client().get("/items/999").status_code == 404


def test_validation_rejects_bad_payload() -> None:
    api = client()
    assert api.post("/items", json={"name": "", "price": 1}).status_code == 422
    assert api.post("/items", json={"name": "ok", "price": -1}).status_code == 422
