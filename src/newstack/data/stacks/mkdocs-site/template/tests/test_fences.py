"""The docs checker has to fail on bad docs, or it is decoration."""

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_fences", ROOT / "tools" / "check_fences.py")
assert SPEC and SPEC.loader
check_fences = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_fences)


def page(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "page.md"
    path.write_text(body, encoding="utf-8")
    return path


def test_a_matching_example_has_no_problems(tmp_path: Path) -> None:
    path = page(tmp_path, "```python\nprint(2 + 2)\n# -> 4\n```\n")
    assert check_fences.check(path) == []


def test_a_wrong_expectation_is_reported(tmp_path: Path) -> None:
    path = page(tmp_path, "```python\nprint(2 + 2)\n# -> 5\n```\n")
    problems = check_fences.check(path)
    assert len(problems) == 1
    assert "expected ['5'], got ['4']" in problems[0]


def test_a_traceback_is_reported(tmp_path: Path) -> None:
    path = page(tmp_path, "```python\nraise ValueError(\"nope\")\n# -> whatever\n```\n")
    problems = check_fences.check(path)
    assert len(problems) == 1
    assert "example raised ValueError: nope" in problems[0]


def test_blocks_share_a_namespace_within_a_page(tmp_path: Path) -> None:
    body = "```python\nx = 21\n```\n\n```python\nprint(x * 2)\n# -> 42\n```\n"
    assert check_fences.check(page(tmp_path, body)) == []


def test_every_page_in_this_repository_matches() -> None:
    problems = [
        problem
        for path in sorted((ROOT / "docs").rglob("*.md"))
        for problem in check_fences.check(path)
    ]
    assert problems == []


def test_the_command_line_fails_on_a_broken_page(tmp_path: Path) -> None:
    page(tmp_path, "```python\nprint(1)\n# -> 2\n```\n")
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_fences.py"), str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "problem(s) in 1 page(s)" in result.stderr
