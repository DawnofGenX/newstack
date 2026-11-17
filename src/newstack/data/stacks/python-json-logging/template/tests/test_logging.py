import io
import json

from {{ package_name }} import JsonLogger, redact


def parse(buf):
    return json.loads(buf.getvalue().strip().splitlines()[-1])


def test_basic_keys():
    buf = io.StringIO()
    log = JsonLogger("app", output=buf)
    log.info("hello", user="alice")
    obj = parse(buf)
    assert obj["level"] == "INFO"
    assert obj["logger"] == "app"
    assert obj["message"] == "hello"
    assert obj["user"] == "alice"


def test_redaction():
    buf = io.StringIO()
    log = JsonLogger("app", output=buf)
    log.info("login", password="secret", token="abc", extra={"authorization": "Bearer x"})
    obj = parse(buf)
    assert obj["password"] == "[REDACTED]"
    assert obj["token"] == "[REDACTED]"
    assert obj["extra"]["authorization"] == "[REDACTED]"


def test_level_filtering():
    buf = io.StringIO()
    log = JsonLogger("app", level="WARNING", output=buf)
    log.debug("d")
    log.info("i")
    log.warning("w")
    lines = [ln for ln in buf.getvalue().splitlines() if ln.strip()]
    assert len(lines) == 1
    assert json.loads(lines[0])["message"] == "w"


def test_context_binding_and_child():
    buf = io.StringIO()
    base = JsonLogger("app", output=buf, context={"request_id": "r1"})
    child = base.bind(user="bob")
    child.info("msg")
    obj = parse(buf)
    assert obj["request_id"] == "r1"
    assert obj["user"] == "bob"

    buf2 = io.StringIO()
    c2 = JsonLogger("app", output=buf2).child("worker", job=5)
    c2.info("x")
    obj2 = json.loads(buf2.getvalue().strip())
    assert obj2["logger"] == "app.worker"
    assert obj2["job"] == 5


def test_exception_rendering():
    buf = io.StringIO()
    log = JsonLogger("app", output=buf)
    try:
        raise ValueError("boom")
    except Exception:
        log.exception("failed")
    obj = parse(buf)
    assert "exception" in obj
    assert obj["exception"]["type"] == "ValueError"
    assert "boom" in obj["exception"]["message"]
    assert "Traceback" in obj["exception"]["traceback"]


def test_redact_function():
    assert redact({"password": "x", "a": {"token": "y"}}) == {"password": "[REDACTED]", "a": {"token": "[REDACTED]"}}