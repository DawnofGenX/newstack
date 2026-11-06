"""The command line is a contract: exit codes and the words on each line."""

from __future__ import annotations

import json

from {{ package_name }} import cli as subject

SECRET = "cli-secret"
NOW = 1_780_000_000


def run(argv: list[str]) -> int:
    return subject.main(argv)


def test_sign_prints_the_signature(monkeypatch, capsys) -> None:
    monkeypatch.setattr(subject, "time", type("T", (), {"time": staticmethod(lambda: NOW)}))
    code = run(["sign", "--url", "/a", "--secret", SECRET])
    out = capsys.readouterr().out
    assert code == 0
    assert "algorithm    hmac-sha256" in out
    assert f"timestamp    {NOW}" in out


def test_sign_json_is_a_signature_object(monkeypatch, capsys) -> None:
    monkeypatch.setattr(subject, "time", type("T", (), {"time": staticmethod(lambda: NOW)}))
    assert run(["sign", "--url", "/a", "--secret", SECRET, "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["algorithm"] == "hmac-sha256"
    assert payload["expires"] - payload["timestamp"] == 300


def test_a_host_is_refused_with_exit_two(capsys) -> None:
    code = run(["sign", "--url", "https://example.test/a", "--secret", SECRET,
                "--timestamp", str(NOW)])
    assert code == 2
    assert "sign the path" in capsys.readouterr().err


def test_a_malformed_header_is_refused(capsys) -> None:
    code = run(["sign", "--url", "/a", "--secret", SECRET, "--timestamp", str(NOW),
                "--header", "no-colon"])
    assert code == 2
    assert "name:value" in capsys.readouterr().err


def test_string_prints_the_covered_lines(capsys) -> None:
    assert run(["string", "--url", "/a", "--timestamp", str(NOW)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "hmac-sha256"
    assert lines[2] == "GET"
    assert lines[3] == "/a"
    assert len(lines) == 5


def test_a_good_signature_verifies_with_exit_zero(capsys) -> None:
    signature = subject.sign(SECRET, "GET", "/a", timestamp=NOW)
    code = run(["verify", "--url", "/a", "--secret", SECRET, "--now", str(NOW),
                "--signature", signature.value, "--timestamp", str(NOW),
                "--expires", str(signature.expires)])
    assert code == 0
    assert capsys.readouterr().out.startswith("ok")


def test_a_tampered_url_verifies_with_exit_one(capsys) -> None:
    signature = subject.sign(SECRET, "GET", "/a", timestamp=NOW)
    code = run(["verify", "--url", "/b", "--secret", SECRET, "--now", str(NOW),
                "--signature", signature.value, "--timestamp", str(NOW),
                "--expires", str(signature.expires)])
    assert code == 1
    assert capsys.readouterr().out.startswith("refused")


def test_verifying_from_a_json_file_works(tmp_path, capsys) -> None:
    signature = subject.sign(SECRET, "GET", "/a", timestamp=NOW)
    path = tmp_path / "signature.json"
    path.write_text(json.dumps(signature.as_dict()))
    code = run(["verify", "--url", "/a", "--secret", SECRET, "--now", str(NOW),
                "--signature-file", str(path)])
    assert code == 0


def test_a_missing_json_file_is_exit_two(tmp_path, capsys) -> None:
    code = run(["verify", "--url", "/a", "--secret", SECRET, "--now", str(NOW),
                "--signature-file", str(tmp_path / "absent.json")])
    assert code == 2
    assert "does not exist" in capsys.readouterr().err


def test_verify_without_a_signature_is_exit_two(capsys) -> None:
    code = run(["verify", "--url", "/a", "--secret", SECRET, "--now", str(NOW)])
    assert code == 2
    assert "--signature" in capsys.readouterr().err


def test_the_demo_prints_six_holding_stories(capsys) -> None:
    assert run(["demo"]) == 0
    out = capsys.readouterr().out
    assert out.count("-> holds") == 6
