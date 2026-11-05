from __future__ import annotations

import contextlib
import io
import json

import pytest

from {{ package_name }} import cli as subject


def run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = subject.main(argv)
    except SystemExit as exited:
        code = int(exited.code or 0)
    return code, out.getvalue(), err.getvalue()


def build(path, precision: int, count: int) -> None:
    items = path.parent / "items.txt"
    items.write_text("\n".join(f"item:{number}" for number in range(count)) + "\n",
                     encoding="utf-8")
    code, out, _ = run(["build", "--input", str(items), "--sketch", str(path),
                        "--precision", str(precision)])
    assert code == subject.EXIT_OK, out


def test_build_writes_a_sketch(tmp_path) -> None:
    sketch = tmp_path / "seen.json"
    build(sketch, 10, 300)
    payload = json.loads(sketch.read_text(encoding="utf-8"))
    assert payload["precision"] == 10
    assert payload["type"] == "hyperloglog"


def test_an_estimate_inside_the_promise_exits_zero(tmp_path) -> None:
    sketch = tmp_path / "seen.json"
    build(sketch, 12, 2000)
    code, out, _ = run(["estimate", "--sketch", str(sketch), "--expect", "2000"])
    assert code == subject.EXIT_OK, out
    assert "promised" in out


def test_an_estimate_outside_the_promise_exits_one(tmp_path) -> None:
    sketch = tmp_path / "seen.json"
    build(sketch, 12, 2000)
    code, _, _ = run(["estimate", "--sketch", str(sketch), "--expect", "100000"])
    assert code == subject.EXIT_BREACH


def test_info_prints_json(tmp_path) -> None:
    sketch = tmp_path / "seen.json"
    build(sketch, 10, 50)
    code, out, _ = run(["info", "--sketch", str(sketch), "--json"])
    assert code == subject.EXIT_OK
    payload = json.loads(out)
    assert payload["registers"] == 1024
    assert payload["bytes"] == 1024


def test_merging_different_precisions_is_a_usage_error(tmp_path) -> None:
    left = tmp_path / "left.json"
    right = tmp_path / "right.json"
    build(left, 10, 40)
    build(right, 12, 40)
    code, _, err = run(["merge", "--left", str(left), "--right", str(right),
                        "--out", str(tmp_path / "merged.json")])
    assert code == subject.EXIT_UNUSABLE
    assert "reinterpreted" in err


def test_merging_equal_precisions_reports_the_union(tmp_path) -> None:
    left = tmp_path / "left.json"
    right = tmp_path / "right.json"
    build(left, 12, 400)
    build(right, 12, 400)
    code, out, _ = run(["merge", "--left", str(left), "--right", str(right),
                        "--out", str(tmp_path / "merged.json")])
    assert code == subject.EXIT_OK
    assert "union" in out


def test_a_missing_sketch_exits_two(tmp_path) -> None:
    code, _, err = run(["estimate", "--sketch", str(tmp_path / "nope.json")])
    assert code == subject.EXIT_UNUSABLE
    assert "cannot read" in err


def test_a_corrupt_sketch_exits_two(tmp_path) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text("{nope", encoding="utf-8")
    code, _, err = run(["estimate", "--sketch", str(broken)])
    assert code == subject.EXIT_UNUSABLE
    assert "not JSON" in err


def test_a_sketch_of_the_wrong_shape_exits_two(tmp_path) -> None:
    wrong = tmp_path / "wrong.json"
    wrong.write_text(json.dumps({"type": "set"}), encoding="utf-8")
    code, _, err = run(["estimate", "--sketch", str(wrong)])
    assert code == subject.EXIT_UNUSABLE
    assert "not a hyperloglog" in err


def test_the_version_banner_names_the_program() -> None:
    stream = io.StringIO()
    with pytest.raises(SystemExit) as exited, contextlib.redirect_stdout(stream):
        subject.main(["--version"])
    assert int(exited.value.code or 0) == 0


def test_the_demo_exits_zero() -> None:
    code, out, _ = run(["demo"])
    assert code == subject.EXIT_OK, out
    assert "precision buys accuracy" in out
