from __future__ import annotations

from pathlib import Path

import pytest

from {{ package_name }} import cli as subject
from {{ package_name }} import verify as verifier

BASE = "".join(f"line {n}\n" for n in range(1, 11))
EDITED = BASE.replace("line 4\n", "line four\n")


def write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8", newline="")
    return path


def test_diff_prints_a_patch(capsys, tmp_path: Path) -> None:
    old = write(tmp_path / "a.txt", BASE)
    new = write(tmp_path / "b.txt", EDITED)
    assert subject.main(["diff", str(old), str(new)]) == 0
    out = capsys.readouterr().out
    assert out.startswith("--- ")
    assert "@@ -1,7 +1,7 @@" in out
    assert "-line 4" in out and "+line four" in out


def test_diff_writes_a_file_and_says_so(capsys, tmp_path: Path) -> None:
    old = write(tmp_path / "a.txt", BASE)
    new = write(tmp_path / "b.txt", EDITED)
    target = tmp_path / "change.patch"
    assert subject.main(["diff", str(old), str(new), "-o", str(target)]) == 0
    err = capsys.readouterr().err
    assert "wrote" in err and "1 hunk(s)" in err
    assert "@@ " in target.read_text(encoding="utf-8")


def test_diff_of_identical_files_says_so(capsys, tmp_path: Path) -> None:
    old = write(tmp_path / "a.txt", BASE)
    assert subject.main(["diff", str(old), str(old)]) == 0
    assert "no differences" in capsys.readouterr().err


def test_apply_prints_the_result(capsys, tmp_path: Path) -> None:
    old = write(tmp_path / "a.txt", BASE)
    new = write(tmp_path / "b.txt", EDITED)
    patch = tmp_path / "change.patch"
    subject.main(["diff", str(old), str(new), "-o", str(patch)])
    capsys.readouterr()
    assert subject.main(["apply", str(old), str(patch)]) == 0
    captured = capsys.readouterr()
    assert captured.out == EDITED
    assert "applied   clean" in captured.err


def test_apply_in_place_rewrites_the_file(capsys, tmp_path: Path) -> None:
    old = write(tmp_path / "a.txt", BASE)
    new = write(tmp_path / "b.txt", EDITED)
    patch = tmp_path / "change.patch"
    subject.main(["diff", str(old), str(new), "-o", str(patch)])
    capsys.readouterr()
    assert subject.main(["apply", str(old), str(patch), "-i"]) == 0
    assert old.read_text(encoding="utf-8") == EDITED


def test_apply_reports_fuzz(capsys, tmp_path: Path) -> None:
    old = write(tmp_path / "a.txt", BASE.replace("line 3\n", "line three\n"))
    patch = write(
        tmp_path / "f.patch",
        "--- a\n+++ b\n@@ -1,3 +1,3 @@\n line 1\n-line 2\n+line two\n line 3\n",
    )
    assert subject.main(["apply", str(old), str(patch), "--fuzz", "1"]) == 0
    assert "with fuzz" in capsys.readouterr().err


def test_check_reports_the_three_claims(capsys, tmp_path: Path) -> None:
    old = write(tmp_path / "a.txt", BASE)
    new = write(tmp_path / "b.txt", EDITED)
    assert subject.main(["check", str(old), str(new)]) == 0
    out = capsys.readouterr().out
    assert out.count("ok  ") == 3
    assert "all three claims hold" in out


def test_check_exits_one_when_a_claim_breaks(monkeypatch, capsys, tmp_path: Path) -> None:
    old = write(tmp_path / "a.txt", BASE)
    new = write(tmp_path / "b.txt", EDITED)
    broken = verifier.Verdict((verifier.Check("x", False, "no"),))
    monkeypatch.setattr(subject, "roundtrip", lambda *_args, **_kwargs: broken)
    assert subject.main(["check", str(old), str(new)]) == 1
    assert "a claim broke" in capsys.readouterr().out


def test_a_malformed_patch_is_unusable(capsys, tmp_path: Path) -> None:
    old = write(tmp_path / "a.txt", BASE)
    patch = write(tmp_path / "bad.patch", "hello\n")
    assert subject.main(["apply", str(old), str(patch)]) == 2
    assert "not a unified diff" in capsys.readouterr().err


def test_a_missing_file_is_unusable(capsys, tmp_path: Path) -> None:
    assert subject.main(["diff", str(tmp_path / "nope"), str(tmp_path / "nope2")]) == 2
    assert "cannot read" in capsys.readouterr().err


def test_demo_and_selftest_pass(capsys) -> None:
    assert subject.main(["demo"]) == 0
    assert "0 not as advertised" in capsys.readouterr().out
    assert subject.main(["selftest"]) == 0
    assert "0 failed" in capsys.readouterr().out


def test_version_is_reported() -> None:
    with pytest.raises(SystemExit) as caught:
        subject.main(["--version"])
    assert caught.value.code == 0


def test_a_command_is_required() -> None:
    with pytest.raises(SystemExit) as caught:
        subject.main([])
    assert caught.value.code == 2
