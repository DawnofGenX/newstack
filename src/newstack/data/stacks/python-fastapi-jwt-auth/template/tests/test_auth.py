import os

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("AUTH_USERS", '{"alice": "wonderland"}')

from fastapi.testclient import TestClient

from {{ package_name }}.main import create_app


def client():
    return TestClient(create_app())


def test_health():
    c = client()
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_login_form_and_me():
    c = client()
    r = c.post("/token", data={"username": "alice", "password": "wonderland"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    r2 = c.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert r2.json()["user"] == "alice"


def test_login_json():
    c = client()
    r = c.post("/token", json={"username": "alice", "password": "wonderland"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_bad_credentials_401():
    c = client()
    r = c.post("/token", data={"username": "alice", "password": "wrong"})
    assert r.status_code == 401
    assert "WWW-Authenticate" in r.headers


def test_missing_token_401():
    c = client()
    r = c.get("/me")
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "Bearer"


def test_tampered_token_401():
    c = client()
    r = c.post("/token", data={"username": "alice", "password": "wonderland"})
    token = r.json()["access_token"]
    tampered = token[:-4] + "aaaa"
    r2 = c.get("/me", headers={"Authorization": f"Bearer {tampered}"})
    assert r2.status_code == 401


def test_expired_token_401(monkeypatch):
    import jwt

    token = jwt.encode({"sub": "alice", "iat": 0, "exp": 1}, "test-secret", algorithm="HS256")
    c = client()
    r = c.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401