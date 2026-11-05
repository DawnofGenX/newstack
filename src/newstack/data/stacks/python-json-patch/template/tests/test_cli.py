from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

from {{ package_name }} import cli as subject

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
DOCUMENT = str(FIXTURES / "document.json")
CHANGES = str(FIXTURES / "changes.json")
AFTER = str(FIXTURES / "after.json")


def run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = subject.main(argv)
    except SystemExit as exited:
        code = int(exited.code or 0)
    return code, out.getvalue(), err.getvalue()


def test_apply_prints_the_result() -> None:
    code, out, _ = run(["apply", "--document", DOCUMENT, "--patch", CHANGES])
    assert code == subject.EXIT_OK
    assert "operations   7" in out
    assert '"slug": "orders"' in out


def test_apply_json_prints_only_the_document() -> None:
    code, out, _ = run(["apply", "--document", DOCUMENT, "--patch", CHANGES, "--json"])
    assert code == subject.EXIT_OK
    assert json.loads(out)["version"] == 4


def test_check_leaves_the_document_alone() -> None:
    before = Path(DOCUMENT).read_text()
    code, out, _ = run(["check", "--document", DOCUMENT, "--patch", CHANGES])
    assert code == subject.EXIT_OK
    assert "unchanged" in out
    assert Path(DOCUMENT).read_text() == before


def test_a_failing_test_exits_one(tmp_path) -> None:
    patch = tmp_path / "patch.json"
    patch.write_text(json.dumps([{"op": "test", "path": "/version", "value": 99}]))
    code, _, err = run(["apply", "--document", DOCUMENT, "--patch", str(patch)])
    assert code == subject.EXIT_REFUSED
    assert "test failed" in err


def test_an_unreadable_document_exits_two() -> None:
    code, _, err = run(["apply", "--document", "/nope.json", "--patch", CHANGES])
    assert code == subject.EXIT_UNUSABLE
    assert "cannot read" in err


def test_resolve_reads_one_pointer() -> None:
    code, out, _ = run(["resolve", "--document", DOCUMENT, "/meta/m~0n"])
    assert code == subject.EXIT_OK
    assert '"tilde"' in out


def test_a_bad_pointer_exits_two() -> None:
    code, _, err = run(["resolve", "--document", DOCUMENT, "/meta~2n"])
    assert code == subject.EXIT_UNUSABLE
    assert "error:" in err


def test_diff_prints_the_operations_and_proves_them() -> None:
    code, out, _ = run(["diff", "--before", DOCUMENT, "--after", AFTER])
    assert code == subject.EXIT_OK
    assert "operations   7" in out
    assert "applies      True" in out


def test_diff_json_is_a_patch() -> None:
    code, out, _ = run(["diff", "--before", DOCUMENT, "--after", AFTER, "--json"])
    assert code == subject.EXIT_OK
    operations = json.loads(out)
    assert operations[0]["op"] == "replace"
    assert all("path" in operation for operation in operations)


def test_the_demo_holds_every_story() -> None:
    code, out, _ = run(["demo"])
    assert code == subject.EXIT_OK
    assert out.count("-> holds") == 6
    assert "BROKEN" not in out


def test_version_names_the_program() -> None:
    code, out, _ = run(["--version"])
    assert code == 0
    assert subject.PROGRAM in out
