"""``newstack update``: three-way merge of recorded, disk and template."""

from __future__ import annotations

import json

from newstack.cli import main
from newstack.upgrade import RECORD_NAME, read_record, sha256_bytes

README = "# {{title}}\n\n{{description}}\n"
INIT = '"""{{project_name}}"""\n'


def _stack(tmp_path, monkeypatch):
    """A tiny stack we can edit between runs, registered through the env var."""
    root = tmp_path / "stacks"
    stack = root / "mini"
    template = stack / "template"
    (template / "src" / "{{package_name}}").mkdir(parents=True)
    (stack / "stack.json").write_text(
        json.dumps(
            {
                "name": "mini",
                "title": "Mini",
                "language": "python",
                "blurb": "a tiny stack for update tests",
                "requires": [],
            }
        ),
        encoding="utf-8",
    )
    (template / "README.md").write_text(README, encoding="utf-8")
    (template / "src" / "{{package_name}}" / "__init__.py").write_text(
        INIT, encoding="utf-8"
    )
    monkeypatch.setenv("NEWSTACK_STACKS", str(root))
    return template


def _project(tmp_path, monkeypatch):
    template = _stack(tmp_path, monkeypatch)
    dest = tmp_path / "proj"
    assert main(["new", "mini", str(dest), "--no-git"]) == 0
    return template, dest


def test_new_records_every_file_it_wrote(tmp_path, monkeypatch) -> None:
    template, dest = _project(tmp_path, monkeypatch)

    record = read_record(dest)
    assert record is not None
    assert record.stack == "mini"
    assert record.context["project_name"] == "proj"
    assert record.files
    for rel, digest in record.files.items():
        assert sha256_bytes((dest / rel).read_bytes()) == digest, rel
    assert set(record.files) == {
        "LICENSE",  # written from the licence registry, not from the template
        "README.md",
        "src/proj/__init__.py",
    }
    assert (dest / RECORD_NAME).is_file()


def test_update_is_a_noop_on_a_fresh_project(tmp_path, monkeypatch, capsys) -> None:
    _template, dest = _project(tmp_path, monkeypatch)
    before = {p: p.read_bytes() for p in dest.rglob("*") if p.is_file()}

    assert main(["update", str(dest)]) == 0
    out = capsys.readouterr().out
    assert "up to date" in out

    after = {p: p.read_bytes() for p in dest.rglob("*") if p.is_file()}
    assert after == before


def test_update_refreshes_a_file_nobody_touched(tmp_path, monkeypatch) -> None:
    template, dest = _project(tmp_path, monkeypatch)
    (template / "README.md").write_text(README + "\nInstall it.\n", encoding="utf-8")

    assert main(["update", str(dest)]) == 0
    assert "Install it." in (dest / "README.md").read_text(encoding="utf-8")
    assert (dest / "src" / "proj" / "__init__.py").read_text(encoding="utf-8") == INIT.replace(
        "{{project_name}}", "proj"
    )


def test_update_keeps_a_local_edit_and_exits_1(tmp_path, monkeypatch, capsys) -> None:
    template, dest = _project(tmp_path, monkeypatch)
    (dest / "README.md").write_text("# mine\n", encoding="utf-8")
    (template / "README.md").write_text(README + "\nInstall it.\n", encoding="utf-8")

    assert main(["update", str(dest)]) == 1
    out = capsys.readouterr().out
    assert "conflict" in out and "README.md" in out
    assert (dest / "README.md").read_text(encoding="utf-8") == "# mine\n"

    # The conflict must stay a conflict: our hash is not overwritten with theirs.
    assert read_record(dest).files["README.md"] != sha256_bytes(b"# mine\n")
    assert main(["update", str(dest)]) == 1


def test_update_force_takes_the_template_version(tmp_path, monkeypatch) -> None:
    template, dest = _project(tmp_path, monkeypatch)
    (dest / "README.md").write_text("# mine\n", encoding="utf-8")
    (template / "README.md").write_text("# upstream\n", encoding="utf-8")

    assert main(["update", str(dest), "--force"]) == 0
    assert (dest / "README.md").read_text(encoding="utf-8") == "# upstream\n"
    record = read_record(dest)
    assert record.files["README.md"] == sha256_bytes(b"# upstream\n")


def test_update_adds_files_the_template_gained(tmp_path, monkeypatch) -> None:
    template, dest = _project(tmp_path, monkeypatch)
    extra = template / "docs" / "{{package_name}}-notes.md"
    extra.parent.mkdir()
    extra.write_text("# {{title}} notes\n", encoding="utf-8")

    assert main(["update", str(dest)]) == 0
    written = dest / "docs" / "proj-notes.md"
    assert written.read_text(encoding="utf-8") == "# Proj notes\n"
    assert "docs/proj-notes.md" in read_record(dest).files


def test_prune_deletes_only_untouched_orphans(tmp_path, monkeypatch, capsys) -> None:
    template, dest = _project(tmp_path, monkeypatch)
    extra = template / "old.txt"
    extra.write_text("gone upstream\n", encoding="utf-8")
    assert main(["update", str(dest)]) == 0
    assert (dest / "old.txt").is_file()

    # Drop it upstream, and edit a second copy of it locally.
    (template / "README.md").write_text(README, encoding="utf-8")
    (template / "kept.txt").write_text("kept upstream\n", encoding="utf-8")
    assert main(["update", str(dest)]) == 0
    (dest / "kept.txt").write_text("edited by me\n", encoding="utf-8")

    extra.unlink()
    (template / "kept.txt").unlink()

    capsys.readouterr()
    assert main(["update", str(dest)]) == 0
    out = capsys.readouterr().out
    assert "orphaned" in out and "kept.txt" in out
    assert (dest / "old.txt").is_file(), "no --prune: nothing is deleted"
    assert (dest / "kept.txt").read_text(encoding="utf-8") == "edited by me\n"

    assert main(["update", str(dest), "--prune"]) == 0
    assert not (dest / "old.txt").exists()
    assert (dest / "kept.txt").read_text(encoding="utf-8") == "edited by me\n"


def test_dry_run_writes_nothing(tmp_path, monkeypatch, capsys) -> None:
    template, dest = _project(tmp_path, monkeypatch)
    (template / "README.md").write_text("# changed upstream\n", encoding="utf-8")
    (template / "new.txt").write_text("new\n", encoding="utf-8")
    record_before = (dest / RECORD_NAME).read_bytes()

    assert main(["update", str(dest), "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "would write" in out
    assert (dest / "README.md").read_text(encoding="utf-8") == README.replace(
        "{{title}}", "Proj"
    ).replace("{{description}}", "A Mini project.")
    assert not (dest / "new.txt").exists()
    assert (dest / RECORD_NAME).read_bytes() == record_before


def test_update_without_a_record_needs_a_stack(tmp_path, monkeypatch, capsys) -> None:
    _stack(tmp_path, monkeypatch)
    dest = tmp_path / "plain"
    dest.mkdir()
    (dest / "README.md").write_text("# handwritten\n", encoding="utf-8")

    assert main(["update", str(dest)]) == 1
    assert "no .newstack.json" in capsys.readouterr().err

    # With --stack it can still work, but a file it never wrote is a conflict.
    assert main(["update", str(dest), "--stack", "mini"]) == 1
    out = capsys.readouterr().out
    assert "README.md" in out and "not written by newstack" in out
    assert (dest / "README.md").read_text(encoding="utf-8") == "# handwritten\n"


def test_update_without_a_record_adds_missing_files(tmp_path, monkeypatch) -> None:
    _stack(tmp_path, monkeypatch)
    dest = tmp_path / "plain"
    dest.mkdir()

    assert main(["update", str(dest), "--stack", "mini"]) == 0
    assert (dest / "src" / "plain" / "__init__.py").read_text(encoding="utf-8") == (
        '"""plain"""\n'
    )
    assert not (dest / RECORD_NAME).exists(), "no record to merge against"


def test_outdated_is_quiet_on_a_fresh_project(tmp_path, monkeypatch, capsys) -> None:
    _, dest = _project(tmp_path, monkeypatch)

    assert main(["outdated", str(dest)]) == 0
    assert "up to date" in capsys.readouterr().out


def test_outdated_reports_what_update_would_do(tmp_path, monkeypatch, capsys) -> None:
    template, dest = _project(tmp_path, monkeypatch)
    (template / "README.md").write_text("# newer upstream\n", encoding="utf-8")
    (template / "extra.txt").write_text("new\n", encoding="utf-8")
    (dest / "src" / "proj" / "__init__.py").write_text("edited\n", encoding="utf-8")

    assert main(["outdated", str(dest)]) == 1
    out = capsys.readouterr().out
    assert "behind" in out and "README.md" in out
    assert "missing" in out and "extra.txt" in out
    assert "modified" in out and "src/proj/__init__.py" in out
    assert (dest / "README.md").read_text(encoding="utf-8").startswith("# Proj")
    assert not (dest / "extra.txt").exists(), "outdated must never write"


def test_outdated_json_is_scriptable(tmp_path, monkeypatch, capsys) -> None:
    template, dest = _project(tmp_path, monkeypatch)
    capsys.readouterr()  # drop the `new` report so only the JSON is parsed
    (template / "README.md").write_text("# newer upstream\n", encoding="utf-8")

    assert main(["outdated", str(dest), "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["updates_available"] is True
    assert payload["behind"] == ["README.md"]
    assert payload["missing"] == []


def test_outdated_needs_a_record(tmp_path, monkeypatch, capsys) -> None:
    _stack(tmp_path, monkeypatch)
    dest = tmp_path / "plain"
    dest.mkdir()

    assert main(["outdated", str(dest)]) == 1
    assert "no .newstack.json" in capsys.readouterr().err
