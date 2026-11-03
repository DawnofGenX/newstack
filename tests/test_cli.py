from __future__ import annotations

import json

from newstack.cli import main


def test_list_text_lists_every_stack(capsys) -> None:
    assert main(["list"]) == 0
    out = capsys.readouterr().out
    for name in ("python-lib", "python-cli", "fastapi", "react-vite-ts", "node-express-ts"):
        assert name in out


def test_list_json_is_machine_readable(capsys) -> None:
    assert main(["list", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload) >= 6
    assert {"name", "title", "language", "blurb", "requires"} <= set(payload[0])


def test_version(capsys) -> None:
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip().count(".") == 2


def test_doctor_reports_toolchains(capsys) -> None:
    assert main(["doctor"]) == 0
    assert "stacks can be verified" in capsys.readouterr().out


def test_new_generates_project(tmp_path, capsys) -> None:
    dest = tmp_path / "mylib"
    code = main(["new", "python-lib", str(dest), "--name", "mylib", "-d", "Demo", "--no-git"])
    assert code == 0
    assert (dest / "pyproject.toml").is_file()
    assert (dest / "src/mylib/core.py").is_file()
    assert "mylib" in (dest / "README.md").read_text()
    assert 'name = "mylib"' in (dest / "pyproject.toml").read_text()
    assert "created" in capsys.readouterr().out


def test_new_json_output(tmp_path, capsys) -> None:
    dest = tmp_path / "api"
    code = main(["new", "fastapi", str(dest), "--no-git", "--json"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["stack"] == "fastapi"
    assert len(payload["files"]) >= 5
    assert payload["git"] is None


def test_new_dry_run_writes_nothing(tmp_path) -> None:
    dest = tmp_path / "ghost"
    assert main(["new", "python-cli", str(dest), "--dry-run"]) == 0
    assert not dest.exists()


def test_new_rejects_unknown_stack(tmp_path, capsys) -> None:
    assert main(["new", "nope", str(tmp_path / "x")]) == 1
    assert "unknown stack" in capsys.readouterr().err


def test_new_rejects_bad_project_name(tmp_path, capsys) -> None:
    assert main(["new", "python-lib", str(tmp_path / "x"), "--name", "has space"]) == 1
    assert "invalid project name" in capsys.readouterr().err


def test_new_refuses_to_overwrite(tmp_path, capsys) -> None:
    dest = tmp_path / "taken"
    dest.mkdir()
    (dest / "keep.txt").write_text("mine")
    assert main(["new", "python-lib", str(dest), "--no-git"]) == 1
    assert "not empty" in capsys.readouterr().err


def test_package_name_sanitises_awkward_names(tmp_path) -> None:
    leading_digit = tmp_path / "digit"
    assert main(["new", "python-lib", str(leading_digit), "--name", "2fast", "--no-git"]) == 0
    assert (leading_digit / "src/app_2fast").is_dir()

    reserved = tmp_path / "keyword"
    assert main(["new", "python-lib", str(reserved), "--name", "class", "--no-git"]) == 0
    assert (reserved / "src/class_app").is_dir()


def test_check_unknown_stack_errors(capsys) -> None:
    assert main(["check", "nope"]) == 1
    assert "unknown stack" in capsys.readouterr().err


def test_check_without_arguments_errors(capsys) -> None:
    assert main(["check"]) == 1
    assert "at least one stack" in capsys.readouterr().err


def test_generated_project_has_no_unresolved_placeholders(tmp_path) -> None:
    import re

    for stack in ("python-lib", "python-cli", "fastapi", "react-vite-ts", "node-express-ts"):
        dest = tmp_path / stack
        assert main(["new", stack, str(dest), "--no-git", "--json"]) == 0
        for path in dest.rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="ignore")
                assert not re.search(r"(?<!\$)\{\{", text), f"{stack}:{path}"


def _half_built_stack(tmp_path, monkeypatch):
    root = tmp_path / "stacks"
    broken = root / "half-built"
    broken.mkdir(parents=True)
    (broken / "stack.json").write_text(
        '{"name": "half-built", "title": "Half", "language": "go", "blurb": "wip"}',
        encoding="utf-8",
    )
    monkeypatch.setenv("NEWSTACK_STACKS", str(root))
    return broken


def test_list_survives_a_half_built_stack(tmp_path, monkeypatch, capsys) -> None:
    _half_built_stack(tmp_path, monkeypatch)
    assert main(["list"]) == 0
    captured = capsys.readouterr()
    assert "half-built" in captured.err
    assert "missing template/" in captured.err
    assert "stacks available" in captured.out


def test_check_all_fails_on_an_unusable_stack_directory(tmp_path, monkeypatch, capsys) -> None:
    _half_built_stack(tmp_path, monkeypatch)

    class _Pass:
        ok = True
        seconds = 0.0
        outcomes: list = []
        directory = None

        def as_dict(self):
            return {}

    monkeypatch.setattr("newstack.cli.check_stack", lambda *a, **k: _Pass())
    monkeypatch.setattr("newstack.cli.missing_tools", lambda stack: [])

    assert main(["check", "--all"]) == 1
    out = capsys.readouterr().out
    assert "half-built" in out and "unusable" in out
