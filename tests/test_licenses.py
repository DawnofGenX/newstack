"""``--license``: the generated LICENSE file, and the record that protects it."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from newstack import licenses
from newstack.cli import main
from newstack.registry import load_stacks
from newstack.upgrade import read_record

YEAR = str(datetime.now(timezone.utc).date().year)
AUTHOR = "Ada Lovelace"

LICENSED_STACKS = [
    stack for stack in load_stacks().values() if (stack.template_dir / "LICENSE").is_file()
]


def _new(tmp_path: Path, stack: str = "python-cli", *extra: str) -> Path:
    dest = tmp_path / "proj"
    code = main(
        [
            "new",
            stack,
            str(dest),
            "--name",
            "proj",
            "--author",
            AUTHOR,
            "--no-git",
            *extra,
        ]
    )
    assert code == 0
    return dest


def _render(key: str, context: dict) -> str:
    """The licence body with its placeholders filled in, independently of the renderer."""
    body = licenses.text(key)
    for name, value in context.items():
        body = body.replace("{{ " + name + " }}", str(value))
    return body


def test_default_licence_is_the_mit_text_the_templates_ship(tmp_path: Path) -> None:
    dest = _new(tmp_path)
    written = (dest / "LICENSE").read_text(encoding="utf-8")
    assert written.startswith("MIT License\n")
    assert f"Copyright (c) {YEAR} {AUTHOR}" in written
    assert "{{" not in written
    assert written == _render("mit", {"year": YEAR, "author": AUTHOR})


@pytest.mark.parametrize("stack", LICENSED_STACKS, ids=lambda stack: stack.name)
def test_every_template_licence_matches_the_registry(stack) -> None:
    """Templates keep a copy of the MIT text; it must not drift from data/licenses."""
    shipped = (stack.template_dir / "LICENSE").read_bytes()
    assert shipped == licenses.text("mit").encode("utf-8"), (
        f"{stack.name}/template/LICENSE drifted from data/licenses/mit.txt"
    )


def test_apache_is_written_when_asked(tmp_path: Path) -> None:
    dest = _new(tmp_path, "python-cli", "--license", "apache-2.0")
    written = (dest / "LICENSE").read_text(encoding="utf-8")
    assert written.startswith("                                 Apache License\n")
    assert "Version 2.0, January 2004" in written
    assert f"Copyright {YEAR} {AUTHOR}" in written
    assert "http://www.apache.org/licenses/LICENSE-2.0" in written
    assert "[yyyy]" not in written and "[name of copyright owner]" not in written
    assert "{{" not in written
    assert written.endswith("limitations under the License.\n")


def test_bsd_three_clause_is_written_when_asked(tmp_path: Path) -> None:
    dest = _new(tmp_path, "python-cli", "--license", "bsd-3")
    written = (dest / "LICENSE").read_text(encoding="utf-8")
    assert written.startswith("BSD 3-Clause License\n")
    assert f"Copyright (c) {YEAR} {AUTHOR}" in written
    assert "3. Neither the name of the copyright holder" in written
    assert "{{" not in written


def test_licence_none_ships_no_file(tmp_path: Path) -> None:
    dest = _new(tmp_path, "python-cli", "--license", "none")
    assert not (dest / "LICENSE").exists()
    record = read_record(dest)
    assert record is not None
    assert record.context["license"] == "none"
    assert "LICENSE" not in record.files


def test_a_stack_without_a_template_licence_still_gets_one(tmp_path: Path) -> None:
    """astro ships no LICENSE; the default licence fills the gap for every stack."""
    dest = _new(tmp_path, "astro")
    assert (dest / "LICENSE").read_text(encoding="utf-8").startswith("MIT License\n")


def test_unknown_licence_is_refused_before_anything_is_written(tmp_path: Path) -> None:
    dest = tmp_path / "proj"
    with pytest.raises(SystemExit) as excinfo:
        main(["new", "python-cli", str(dest), "--license", "gpl-3.0", "--no-git"])
    assert excinfo.value.code == 2
    assert not dest.exists()


def test_the_record_remembers_the_licence_so_update_leaves_it_alone(
    tmp_path: Path, capsys
) -> None:
    dest = _new(tmp_path, "python-cli", "--license", "apache-2.0")
    before = (dest / "LICENSE").read_bytes()

    record = read_record(dest)
    assert record is not None
    assert record.context["license"] == "apache-2.0"

    capsys.readouterr()  # drop the `new` report
    assert main(["update", str(dest)]) == 0
    out = capsys.readouterr().out
    assert "up to date" in out
    assert (dest / "LICENSE").read_bytes() == before


def test_update_can_switch_the_licence(tmp_path: Path, capsys) -> None:
    dest = _new(tmp_path)
    capsys.readouterr()

    assert main(["update", str(dest), "--license", "bsd-3"]) == 0
    out = capsys.readouterr().out
    assert "LICENSE" in out
    assert (dest / "LICENSE").read_text(encoding="utf-8").startswith("BSD 3-Clause License\n")

    record = read_record(dest)
    assert record is not None
    assert record.context["license"] == "bsd-3"


def test_adopt_never_writes_a_licence(tmp_path: Path, capsys) -> None:
    """A licence is a choice, not adoption infrastructure."""
    project = tmp_path / "existing"
    project.mkdir()
    (project / "package.json").write_text('{"name": "existing"}', encoding="utf-8")

    assert main(["adopt", str(project), "--stack", "astro", "--dry-run"]) == 0
    assert "LICENSE" not in capsys.readouterr().out

    assert main(["adopt", str(project), "--stack", "astro"]) == 0
    capsys.readouterr()
    assert not (project / "LICENSE").exists()


def test_the_json_report_names_the_licence(tmp_path: Path, capsys) -> None:
    dest = tmp_path / "proj"
    assert main(["new", "python-cli", str(dest), "--license", "bsd-3", "--no-git", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["license"] == "bsd-3"


def test_the_registry_rejects_an_unknown_key() -> None:
    with pytest.raises(licenses.LicenseError):
        licenses.text("wtfpl")


def test_every_licence_body_is_complete_and_has_no_stray_placeholders() -> None:
    for key in licenses.BY_KEY:
        body = licenses.text(key)
        assert body.endswith("\n"), key
        assert body.count("{{ year }}") == 1, key
        assert body.count("{{ author }}") == 1, key
        assert len(body) > 1000, key
