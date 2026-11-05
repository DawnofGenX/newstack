"""The CLI is the thing a pipeline calls, so its exit codes are the contract."""

from __future__ import annotations

import json

import pytest

from {{ package_name }} import audit as audit_mod
from {{ package_name }} import cli as subject


def run(argv: list[str]) -> int:
    return subject.main(argv)


def test_render_reads_stdin(monkeypatch, capsys) -> None:
    import io
    import sys

    monkeypatch.setattr(sys, "stdin", type("In", (), {"buffer": io.BytesIO(b"<b>x</b>")})())
    assert run(["render"]) == subject.EXIT_OK
    captured = capsys.readouterr()
    assert captured.out.strip() == "<b>x</b>"
    assert "dropped" in captured.err


def test_render_reads_a_file(tmp_path, capsys) -> None:
    page = tmp_path / "page.html"
    page.write_text('<p onclick="x">hi</p>', encoding="utf-8")
    assert run(["render", "--file", str(page)]) == subject.EXIT_OK
    assert capsys.readouterr().out.strip() == "<p>hi</p>"


def test_render_json_has_the_output_and_the_counters(tmp_path, capsys) -> None:
    page = tmp_path / "page.html"
    page.write_text('<a href="javascript:1">x</a>', encoding="utf-8")
    assert run(["render", "--file", str(page), "--json"]) == subject.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["output"] == "<a>x</a>"
    assert payload["stats"]["urls_refused"] == 1


def test_render_of_a_missing_file_is_exit_two(capsys) -> None:
    assert run(["render", "--file", "/nope/none.html"]) == subject.EXIT_UNUSABLE
    assert "cannot read" in capsys.readouterr().err


def test_check_passes_a_clean_corpus(tmp_path, capsys) -> None:
    page = tmp_path / "page.html"
    page.write_text("<b>x</b>", encoding="utf-8")
    assert run(["check", str(page)]) == subject.EXIT_OK
    assert capsys.readouterr().out.startswith("ok")


def test_check_fails_when_the_audit_fails(tmp_path, capsys, monkeypatch) -> None:
    page = tmp_path / "page.html"
    page.write_text("<b>x</b>", encoding="utf-8")

    class Bad:
        ok = False
        idempotent = True
        problems = ("script tag in '<script>'",)

        def as_dict(self) -> dict[str, object]:
            return {"ok": False}

    monkeypatch.setattr(subject, "audit", lambda text, policy=None: Bad())
    assert run(["check", str(page)]) == subject.EXIT_PROBLEM
    captured = capsys.readouterr()
    assert "FAIL" in captured.out
    assert "script tag" in captured.out


def test_check_json_rows_report_each_file(tmp_path, capsys) -> None:
    page = tmp_path / "page.html"
    page.write_text("<b>x</b>", encoding="utf-8")
    assert run(["check", str(page), "--json"]) == subject.EXIT_OK
    out = capsys.readouterr().out
    rows = json.loads(out[out.index("[") :])
    assert rows[0]["ok"] is True


def test_policy_prints_the_allowlist(capsys) -> None:
    assert run(["policy"]) == subject.EXIT_OK
    out = capsys.readouterr().out
    assert out.startswith("tags")
    assert "a: href title" in out
    assert "schemes  http https mailto tel" in out


def test_demo_exits_zero(capsys) -> None:
    assert run(["demo"]) == subject.EXIT_OK
    assert "0 not as advertised" in capsys.readouterr().out


def test_selftest_exits_zero(capsys) -> None:
    assert run(["selftest"]) == subject.EXIT_OK
    assert "0 failed" in capsys.readouterr().out


def test_no_command_is_exit_two(capsys) -> None:
    assert run([]) == subject.EXIT_UNUSABLE
    assert "usage" in capsys.readouterr().err


def test_version_exits_zero(capsys) -> None:
    with pytest.raises(SystemExit) as caught:
        run(["--version"])
    assert caught.value.code == 0
    assert subject.VERSION in capsys.readouterr().out


def test_the_module_runs_with_dash_m(tmp_path, capsys) -> None:
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "{{ package_name }}", "demo"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "demo:" in result.stdout


def test_the_audit_import_is_the_one_the_cli_uses() -> None:
    assert subject.audit is audit_mod.audit
