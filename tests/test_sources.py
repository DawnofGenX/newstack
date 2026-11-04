"""Installing stacks from a repository: ``newstack stacks add``."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from newstack import sources
from newstack.cli import main
from newstack.registry import load_stacks

GIT_ENV = ("-c", "user.name=test", "-c", "user.email=test@example.com")


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _write_stack(directory: Path, name: str = "mini-cli", *, blurb: str = "Tiny CLI.") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "template").mkdir(exist_ok=True)
    manifest = {
        "name": name,
        "title": name.replace("-", " ").title(),
        "language": "mini",
        "blurb": blurb,
        "requires": [],
        "detect": [{"file": "mini.toml"}],
        "adopt": [".gitignore"],
        "next_steps": ["echo hello"],
        "verify": [{"name": "test", "cmd": "echo checked"}],
    }
    (directory / "stack.json").write_text(json.dumps(manifest), encoding="utf-8")
    (directory / "template" / "README.md").write_text("# {{ npm_name }}\n", encoding="utf-8")
    (directory / "template" / "mini.toml").write_text(
        'name = "{{ npm_name }}"\n', encoding="utf-8"
    )
    (directory / "template" / ".gitignore").write_text("build/\n", encoding="utf-8")


def _repo(tmp_path: Path, layout: str = "nested", names: tuple[str, ...] = ("mini-cli",)) -> Path:
    """A local git repository carrying one or more stacks."""
    repo = tmp_path / "repo"
    repo.mkdir()
    for name in names:
        if layout == "nested":
            _write_stack(repo / name, name)
        elif layout == "root":
            _write_stack(repo, name)
        elif layout == "stacks-dir":
            _write_stack(repo / "stacks" / name, name)
        elif layout == "examples":
            _write_stack(repo / "examples" / name, name)
        else:  # pragma: no cover - guard against a typo in a test
            raise AssertionError(layout)
    _git(["init", "-q", "-b", "main"], repo)
    _git([*GIT_ENV, "add", "-A"], repo)
    _git([*GIT_ENV, "commit", "-qm", "add stacks"], repo)
    return repo


def test_add_installs_a_stack_and_records_where_it_came_from(tmp_path, capsys):
    repo = _repo(tmp_path)

    assert main(["stacks", "add", str(repo)]) == 0
    output = capsys.readouterr().out

    installed = sources.installed_root() / "mini-cli"
    assert (installed / "stack.json").is_file()
    assert (installed / "template" / "README.md").is_file()
    assert ".git" not in {path.name for path in installed.iterdir()}
    assert "installed 1 stack" in output
    assert str(repo) in output
    # the warning about unverified stacks is the point of the command
    assert "not covered by newstack's CI" in output

    assert "mini-cli" in load_stacks()
    assert load_stacks()["mini-cli"].installed is True
    assert load_stacks()["python-cli"].installed is False

    recorded = sources.read_installed()["mini-cli"]
    assert recorded["url"] == str(repo)
    assert len(recorded["rev"]) >= 7
    assert recorded["added_at"].endswith("+00:00")


def test_an_installed_stack_scaffolds_like_a_shipped_one(tmp_path):
    repo = _repo(tmp_path)
    assert main(["stacks", "add", str(repo)]) == 0

    destination = tmp_path / "project"
    assert main(["new", "mini-cli", str(destination), "--no-git"]) == 0

    assert (destination / "README.md").read_text(encoding="utf-8") == "# project\n"
    assert (destination / "mini.toml").read_text(encoding="utf-8") == 'name = "project"\n'
    assert (destination / ".gitignore").is_file()


def test_a_stack_at_the_root_of_the_repository_installs(tmp_path):
    repo = _repo(tmp_path, layout="root")
    assert main(["stacks", "add", str(repo)]) == 0
    assert (sources.installed_root() / "mini-cli" / "stack.json").is_file()


def test_a_repository_with_a_stacks_directory_installs_its_children(tmp_path):
    repo = _repo(tmp_path, layout="stacks-dir")
    assert main(["stacks", "add", str(repo)]) == 0
    assert (sources.installed_root() / "mini-cli" / "stack.json").is_file()


def test_dir_points_at_a_subdirectory_of_the_repository(tmp_path):
    repo = _repo(tmp_path, layout="examples", names=("alpha-cli", "beta-cli"))
    # without --dir the examples/ directory is still found one level down
    assert main(["stacks", "add", str(repo)]) == 0
    assert sources.list_installed()[0].name in {"alpha-cli", "beta-cli"}

    for name in ("alpha-cli", "beta-cli"):
        assert main(["stacks", "remove", name]) == 0
    assert main(["stacks", "add", str(repo), "--dir", "examples"]) == 0
    assert {item.name for item in sources.list_installed()} == {"alpha-cli", "beta-cli"}

    missing = main(["stacks", "add", str(repo), "--dir", "nope"])
    assert missing == 1


def test_a_name_that_ships_with_newstack_is_refused(tmp_path, capsys):
    repo = _repo(tmp_path, layout="root", names=("python-cli",))

    assert main(["stacks", "add", str(repo)]) == 1
    assert "already ships with newstack" in capsys.readouterr().err
    assert not (sources.installed_root() / "python-cli").exists()


def test_one_broken_stack_installs_nothing(tmp_path, capsys):
    repo = _repo(tmp_path, names=("good-cli", "bad-cli"))
    (repo / "bad-cli" / "template").rename(repo / "bad-cli" / "no-template")
    _git([*GIT_ENV, "add", "-A"], repo)
    _git([*GIT_ENV, "commit", "-qm", "break one"], repo)

    assert main(["stacks", "add", str(repo)]) == 1
    assert "missing template/ directory" in capsys.readouterr().err
    assert sources.list_installed() == []


def test_a_repository_without_a_stack_is_refused(tmp_path, capsys):
    repo = tmp_path / "empty"
    repo.mkdir()
    (repo / "README.md").write_text("nothing here\n", encoding="utf-8")
    _git(["init", "-q", "-b", "main"], repo)
    _git([*GIT_ENV, "add", "-A"], repo)
    _git([*GIT_ENV, "commit", "-qm", "init"], repo)

    assert main(["stacks", "add", str(repo)]) == 1
    assert "no stack found" in capsys.readouterr().err


def test_a_bad_url_is_reported_not_raised(tmp_path, capsys):
    assert main(["stacks", "add", str(tmp_path / "missing-repo")]) == 1
    assert "could not clone" in capsys.readouterr().err


def test_reinstalling_needs_force(tmp_path, capsys):
    repo = _repo(tmp_path)
    assert main(["stacks", "add", str(repo)]) == 0
    assert main(["stacks", "add", str(repo)]) == 1
    assert "already installed: mini-cli" in capsys.readouterr().err

    marker = sources.installed_root() / "mini-cli" / "stale.txt"
    marker.write_text("old\n", encoding="utf-8")
    assert main(["stacks", "add", str(repo), "--force"]) == 0
    assert not marker.exists()  # replaced wholesale, not merged into


def test_remove_deletes_an_installed_stack_and_its_record(tmp_path, capsys):
    repo = _repo(tmp_path)
    assert main(["stacks", "add", str(repo)]) == 0

    assert main(["stacks", "remove", "mini-cli"]) == 0
    assert "removed mini-cli" in capsys.readouterr().out
    assert not (sources.installed_root() / "mini-cli").exists()
    assert "mini-cli" not in load_stacks()
    assert sources.read_installed() == {}


def test_a_shipped_stack_cannot_be_removed(tmp_path, capsys):
    assert main(["stacks", "remove", "python-cli"]) == 1
    assert "ships with newstack and cannot be removed" in capsys.readouterr().err
    assert (sources.installed_root() / "python-cli").exists() is False


def test_removing_something_that_is_not_installed_is_an_error(capsys):
    assert main(["stacks", "remove", "nope-cli"]) == 1
    assert "is not installed" in capsys.readouterr().err


def test_list_reports_nothing_installed_then_the_origin(tmp_path, capsys):
    assert main(["stacks", "list"]) == 0
    assert "no stacks installed" in capsys.readouterr().out

    repo = _repo(tmp_path)
    assert main(["stacks", "add", str(repo)]) == 0
    capsys.readouterr()

    assert main(["stacks", "list", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["name"] == "mini-cli"
    assert payload[0]["url"] == str(repo)

    assert main(["stacks", "list"]) == 0
    text = capsys.readouterr().out
    assert "1 installed stack" in text
    assert str(repo) in text


def test_newstack_list_marks_installed_stacks(tmp_path, capsys):
    repo = _repo(tmp_path)
    assert main(["stacks", "add", str(repo)]) == 0
    capsys.readouterr()

    assert main(["list", "--json"]) == 0
    entries = {entry["name"]: entry for entry in json.loads(capsys.readouterr().out)}
    assert entries["mini-cli"]["installed"] is True
    assert entries["python-cli"]["installed"] is False

    assert main(["list"]) == 0
    text = capsys.readouterr().out
    installed_line = next(line for line in text.splitlines() if line.strip().startswith("mini-cli"))
    assert installed_line.endswith("[installed]")
    python_line = next(line for line in text.splitlines() if line.strip().startswith("python-cli"))
    assert "[installed]" not in python_line


def test_an_installed_stack_can_be_checked(tmp_path, capsys):
    repo = _repo(tmp_path)
    assert main(["stacks", "add", str(repo)]) == 0
    capsys.readouterr()

    assert main(["check", "mini-cli"]) == 0
    assert "PASS" in capsys.readouterr().out


def test_install_refuses_without_git(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sources.shutil, "which", lambda name: None)
    assert main(["stacks", "add", str(tmp_path)]) == 1
    assert "git is required" in capsys.readouterr().err


def test_the_suite_never_reads_the_developers_own_installs():
    """A local install must not turn into a parametrised stack in tests/test_stacks.py."""
    import os

    from newstack.registry import installed_root

    assert os.environ["NEWSTACK_HOME"] != str(Path.home() / ".local" / "share" / "newstack")
    assert "pytest" in str(installed_root()) or "newstack-home" in str(installed_root())


@pytest.mark.parametrize("url", ["", "   "])
def test_install_requires_a_url(url, capsys):
    assert main(["stacks", "add", url]) == 1
    assert "repository URL is required" in capsys.readouterr().err
