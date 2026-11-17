"""Catalog drift guards: docs/STACKS.md must track the registry."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from newstack.registry import load_stacks

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "gen_catalog.py"
DOCS = ROOT / "docs" / "STACKS.md"

_spec = importlib.util.spec_from_file_location("gen_catalog", SCRIPT)
assert _spec is not None and _spec.loader is not None
gen_catalog = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen_catalog)


def _generated() -> str:
    return gen_catalog.generate_catalog()


def test_generated_file_matches_script_output() -> None:
    assert DOCS.is_file()
    assert DOCS.read_text(encoding="utf-8") == _generated()


def test_every_stack_appears_exactly_once() -> None:
    text = DOCS.read_text(encoding="utf-8")
    for name in load_stacks():
        assert text.count(f"`{name}`") == 1, (
            f"{name} appears {text.count(f'`{name}`')} times"
        )


def test_language_headings_sorted_and_counts_sum() -> None:
    import re

    text = DOCS.read_text(encoding="utf-8")
    headings = re.findall(r"^##\s+(.+?)\s*\((\d+)\)\s*$", text, re.M)
    assert headings, "no language headings found"
    languages = [language for language, _ in headings]
    assert languages == sorted(languages), "language headings are not sorted"
    assert sum(int(count) for _, count in headings) == len(load_stacks())


def test_check_exits_one_on_stale_copy(tmp_path, monkeypatch) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    stale = docs_dir / "STACKS.md"
    stale.write_text("this is deliberately stale\n", encoding="utf-8")

    monkeypatch.setattr(gen_catalog, "OUTPUT_PATH", stale)
    # keep the other common aliases in sync too
    for alias in ("OUTPUT", "STACKS_MD", "TARGET", "OUT_PATH", "DOC_PATH", "OUTPUT_FILE"):
        monkeypatch.setattr(gen_catalog, alias, stale, raising=False)

    assert gen_catalog.main(["--check"]) == 1


def test_check_exits_zero_when_current(tmp_path, monkeypatch) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    current = docs_dir / "STACKS.md"
    current.write_text(_generated(), encoding="utf-8")

    monkeypatch.setattr(gen_catalog, "OUTPUT_PATH", current)
    for alias in ("OUTPUT", "STACKS_MD", "TARGET", "OUT_PATH", "DOC_PATH", "OUTPUT_FILE"):
        monkeypatch.setattr(gen_catalog, alias, current, raising=False)

    assert gen_catalog.main(["--check"]) == 0


def test_check_verbose_prints_differing_lines(tmp_path, monkeypatch, capsys) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    stale = docs_dir / "STACKS.md"
    stale.write_text("stale content\n", encoding="utf-8")

    monkeypatch.setattr(gen_catalog, "OUTPUT_PATH", stale)
    for alias in ("OUTPUT", "STACKS_MD", "TARGET", "OUT_PATH", "DOC_PATH", "OUTPUT_FILE"):
        monkeypatch.setattr(gen_catalog, alias, stale, raising=False)

    code = gen_catalog.main(["--check", "-v"])
    captured = capsys.readouterr()
    assert code == 1
    assert "stale" in (captured.out + captured.err).lower()
