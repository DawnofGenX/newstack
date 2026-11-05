import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from {{ package_name }} import cli as subject


def run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = subject.main(argv)
    return code, out.getvalue(), err.getvalue()


def test_add_creates_a_sketch(tmp_path: Path) -> None:
    path = tmp_path / "seen.json"
    code, out, _ = run(["add", "--sketch", str(path), "--items", "a", "b", "a"])
    assert code == subject.EXIT_OK
    assert "3 updates" in out
    assert json.loads(path.read_text())["total"] == 3


def test_a_second_add_accumulates(tmp_path: Path) -> None:
    path = tmp_path / "seen.json"
    run(["add", "--sketch", str(path), "--items", "a", "--count", "2", "--width", "64"])
    run(["add", "--sketch", str(path), "--items", "a", "--count", "3"])
    code, out, _ = run(["estimate", "--sketch", str(path), "--item", "a", "--json"])
    assert code == subject.EXIT_OK
    assert json.loads(out)["estimate"] == 5


def test_estimate_names_its_bound(tmp_path: Path) -> None:
    path = tmp_path / "seen.json"
    run(["add", "--sketch", str(path), "--items", "a"])
    code, out, _ = run(["estimate", "--sketch", str(path), "--item", "a"])
    assert code == subject.EXIT_OK
    assert "can be at most" in out


def test_info_prints_the_shape(tmp_path: Path) -> None:
    path = tmp_path / "seen.json"
    run(["add", "--sketch", str(path), "--items", "a", "--width", "64", "--depth", "4"])
    code, out, _ = run(["info", "--sketch", str(path)])
    assert code == subject.EXIT_OK
    assert "width        64" in out
    assert "promise" in out


def test_merge_writes_the_union(tmp_path: Path) -> None:
    left, right, out_path = tmp_path / "l.json", tmp_path / "r.json", tmp_path / "m.json"
    run(["add", "--sketch", str(left), "--items", "a", "--count", "3", "--width", "64"])
    run(["add", "--sketch", str(right), "--items", "a", "--count", "2", "--width", "64"])
    argv = ["merge", "--left", str(left), "--right", str(right), "--out", str(out_path)]
    code, out, _ = run(argv)
    assert code == subject.EXIT_OK
    assert "pointwise" in out
    code, out, _ = run(["estimate", "--sketch", str(out_path), "--item", "a", "--json"])
    assert json.loads(out)["estimate"] == 5


def test_a_missing_sketch_is_unusable(tmp_path: Path) -> None:
    code, _, err = run(["estimate", "--sketch", str(tmp_path / "nope.json"), "--item", "a"])
    assert code == subject.EXIT_UNUSABLE
    assert "does not exist" in err


def test_a_broken_file_is_unusable(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json")
    code, _, err = run(["info", "--sketch", str(path)])
    assert code == subject.EXIT_UNUSABLE
    assert "not JSON" in err


@pytest.mark.parametrize("count", ["0", "-2"])
def test_a_non_positive_count_is_unusable(tmp_path: Path, count: str) -> None:
    code, _, err = run(
        ["add", "--sketch", str(tmp_path / "s.json"), "--items", "a", "--count", count]
    )
    assert code == subject.EXIT_UNUSABLE
    assert "at least 1" in err


def test_mismatched_shapes_are_unusable(tmp_path: Path) -> None:
    left, right = tmp_path / "l.json", tmp_path / "r.json"
    run(["add", "--sketch", str(left), "--items", "a", "--width", "64"])
    run(["add", "--sketch", str(right), "--items", "a", "--width", "128"])
    merged = str(tmp_path / "m.json")
    argv = ["merge", "--left", str(left), "--right", str(right), "--out", merged]
    code, _, err = run(argv)
    assert code == subject.EXIT_UNUSABLE
    assert "would not line up" in err


def test_demo_exits_zero_and_prints_six_stories() -> None:
    code, out, _ = run(["demo"])
    assert code == subject.EXIT_OK
    assert "6. " in out


def test_selftest_passes() -> None:
    code, out, _ = run(["selftest"])
    assert code == subject.EXIT_OK
    assert "checks passed" in out
