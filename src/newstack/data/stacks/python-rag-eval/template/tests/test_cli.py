"""Exit codes are the contract a CI job depends on."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from {{ package_name }} import cli as subject

ROOT = Path(__file__).resolve().parent.parent


def test_eval_prints_the_macro_line(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["eval"]) == subject.EXIT_OK
    printed = capsys.readouterr().out
    assert "macro  recall@3" in printed
    assert "micro  recall@3" in printed
    assert "skip   no judgements" in printed


def test_eval_json_is_machine_readable(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["eval", "--json"]) == subject.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["queries"] == 6
    assert payload["per_query"][0]["query"]


def test_search_ranks_the_expected_document(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["search", "how do I rotate a signing key", "--k", "1"]) == 0
    assert "rotate-key.md" in capsys.readouterr().out


def test_search_with_nothing_in_common_exits_one(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["search", "zebra unicorn"]) == subject.EXIT_REGRESSION
    assert "no chunk shares a word" in capsys.readouterr().err


def test_compare_against_itself_passes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    report = tmp_path / "report.json"
    assert subject.main(["eval", "--json"]) == 0
    report.write_text(capsys.readouterr().out, encoding="utf-8")
    assert subject.main(["compare", "--baseline", str(report), "--candidate", str(report)]) == 0
    assert "no metric dropped" in capsys.readouterr().out


def test_compare_catches_a_dropped_metric(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert subject.main(["eval", "--json"]) == 0
    baseline = json.loads(capsys.readouterr().out)
    candidate = dict(baseline, macro_recall=baseline["macro_recall"] - 0.25)
    paths = []
    for name, payload in (("before.json", baseline), ("after.json", candidate)):
        path = tmp_path / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        paths.append(str(path))
    assert subject.main(["compare", "--baseline", paths[0], "--candidate", paths[1]]) == 1
    assert "DROP macro_recall" in capsys.readouterr().out


def test_compare_tolerance_allows_a_small_drop(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert subject.main(["eval", "--json"]) == 0
    baseline = json.loads(capsys.readouterr().out)
    candidate = dict(baseline, ndcg=baseline["ndcg"] - 0.005)
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    before.write_text(json.dumps(baseline), encoding="utf-8")
    after.write_text(json.dumps(candidate), encoding="utf-8")
    argv = ["compare", "--baseline", str(before), "--candidate", str(after), "--tolerance", "0.01"]
    assert subject.main(argv) == subject.EXIT_OK


def test_a_missing_qrels_file_is_a_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["eval", "--qrels", "nope.json"]) == subject.EXIT_UNUSABLE
    assert "nope.json" in capsys.readouterr().err


def test_a_bad_grade_is_a_usage_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    broken = tmp_path / "qrels.json"
    broken.write_text('{"queries": {"q": {"a.md": -1}}}', encoding="utf-8")
    assert subject.main(["eval", "--qrels", str(broken)]) == subject.EXIT_UNUSABLE


def test_selftest_passes(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["selftest"]) == subject.EXIT_OK
    assert "checks passed" in capsys.readouterr().out
