import pytest

from core.models import Item

pytestmark = pytest.mark.django_db


def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_items_is_empty_without_data(client):
    response = client.get("/items")

    assert response.status_code == 200
    assert response.json() == []


def test_items_lists_created_item(client):
    Item.objects.create(name="Widget")

    response = client.get("/items")

    assert response.status_code == 200
    payload = response.json()
    assert [row["name"] for row in payload] == ["Widget"]
    assert set(payload[0]) == {"id", "name", "created"}
