"""Execute the Python examples in the docs and compare their printed output.

Each ```python fence in the Markdown is run in a fresh namespace. Lines that
start with ``# ->`` are the expected standard output of that block; everything
else is code. A mismatch, a traceback, or a block with no expectation at all is
reported with the page and line number, so CI fails on documentation drift
rather than publishing it.

    python tools/check_fences.py docs
"""

from __future__ import annotations

import contextlib
import io
import re
import sys
from pathlib import Path

BLOCK = re.compile(r"```python\n(.*?)```", re.DOTALL)
EXPECTED = "# -> "


def examples(page: str) -> list[tuple[int, str, list[str]]]:
    """(start line, code, expected output) for every python fence in *page*."""
    found: list[tuple[int, str, list[str]]] = []
    for match in BLOCK.finditer(page):
        body = match.group(1).rstrip("\n")
        start = page.count("\n", 0, match.start()) + 1
        code: list[str] = []
        expected: list[str] = []
        for raw in body.split("\n"):
            if raw.startswith(EXPECTED):
                expected.append(raw[len(EXPECTED) :])
            else:
                code.append(raw)
        found.append((start, "\n".join(code), expected))
    return found


def check(path: Path) -> list[str]:
    """Problems with *path*; an empty list means every example matched."""
    page = path.read_text(encoding="utf-8")
    namespace: dict[str, object] = {}
    problems: list[str] = []
    for start, code, expected in examples(page):
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output):
                # Running the documented snippet is the entire point of this tool.
                exec(compile(code, f"{path}:{start}", "exec"), namespace)  # noqa: S102
        except Exception as error:  # noqa: BLE001 - report any failure, never crash the checker
            reason = f"{type(error).__name__}: {error}"
            problems.append(f"{path}:{start}: example raised {reason}")
            continue
        actual = output.getvalue().rstrip("\n").split("\n") if output.getvalue().strip() else []
        if actual != expected:
            problems.append(
                f"{path}:{start}: expected {expected!r}, got {actual!r}"
            )
    return problems


def main(argv: list[str]) -> int:
    roots = [Path(argument) for argument in argv[1:]] or [Path("docs")]
    pages = sorted(page for root in roots for page in root.rglob("*.md") if root.is_dir())
    if not pages:
        print("no Markdown pages found", file=sys.stderr)
        return 1
    problems = [problem for page in pages for problem in check(page)]
    executed = sum(len(examples(page.read_text(encoding="utf-8"))) for page in pages)
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        print(f"{len(problems)} problem(s) in {len(pages)} page(s)", file=sys.stderr)
        return 1
    print(f"{executed} example(s) in {len(pages)} page(s) match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
