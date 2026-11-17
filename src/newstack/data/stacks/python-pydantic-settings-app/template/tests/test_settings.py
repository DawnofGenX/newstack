from {{ package_name }}.main import load_settings


def test_defaults():
    s = load_settings(env_file=None)
    assert s.host == "127.0.0.1"
    assert s.port == 8000


def test_env_overrides_default(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_PORT", "9100")
    s = load_settings(env_file=None)
    assert s.port == 9100


def test_cli_overrides_env(monkeypatch):
    monkeypatch.setenv("APP_PORT", "9100")
    s = load_settings({"port": 9200}, env_file=None)
    assert s.port == 9200
