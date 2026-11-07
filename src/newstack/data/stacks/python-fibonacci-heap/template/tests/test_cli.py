from __future__ import annotations

import json

import pytest

from {{ package_name }} import cli
from {{ package_name }}.cli import main

FIXTURE = "fixtures/items.txt"
LIVE_KEYS = sorted(
    [
        3, -7, 12, 0, 99, -120, 5, 42, -8, 17, 256, -3, 61, 88, -999, 1024,
    ]
)


def test_version_and_help_exit_zero() -> None:
    assert main(["--version"]) == 0
    assert main(["--help"]) == 0


def test_size_reports_the_live_items(capsys) -> None:
    assert main(["size", "--items", FIXTURE]) == 0
    out = capsys.readouterr().out
    assert "items      16" in out


def test_peek_names_the_next_release(capsys) -> None:
    assert main(["peek", "--items", FIXTURE, "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["min"] == min(LIVE_KEYS)
    assert payload["keys"] == LIVE_KEYS
    assert payload["audit"] == []


def test_push_hands_back_a_handle(capsys) -> None:
    assert main(["push", "--items", FIXTURE, "777"]) == 0
    out = capsys.readouterr().out
    assert "item       17" in out
    assert "items      17" in out


def test_pop_releases_the_smallest(capsys) -> None:
    assert main(["pop", "--items", FIXTURE]) == 0
    out = capsys.readouterr().out
    assert "released   -999" in out
    assert "items      15" in out


def test_decrease_drops_a_tracked_item(capsys) -> None:
    assert main(["decrease", "--items", FIXTURE, "2", "-4000"]) == 0
    out = capsys.readouterr().out
    assert "min        -4000" in out


def test_an_increase_is_refused(capsys) -> None:
    assert main(["decrease", "--items", FIXTURE, "1", "999999"]) == 2
    assert "not a decrease" in capsys.readouterr().err


def test_an_absent_item_is_refused(capsys) -> None:
    assert main(["decrease", "--items", FIXTURE, "99", "5"]) == 2
    assert "no item 99" in capsys.readouterr().err


def test_the_empty_heap_answers_one(tmp_path, capsys) -> None:
    bare = tmp_path / "bare.txt"
    bare.write_text("# nothing\n", encoding="utf-8")
    assert main(["peek", "--items", str(bare)]) == 1
    assert "the heap is empty" in capsys.readouterr().err


def test_a_missing_file_is_unusable(capsys) -> None:
    assert main(["size", "--items", "no/such/items.txt"]) == 2
    assert "no such item list" in capsys.readouterr().err


def test_selftest_and_demo_pass(capsys) -> None:
    assert main(["selftest"]) == 0
    assert "0 failed" in capsys.readouterr().out
    assert main(["demo"]) == 0
    assert "6 of 6 hold" in capsys.readouterr().out


def test_a_bogus_flag_exits_two() -> None:
    with pytest.raises(SystemExit) as request:
        cli.build_parser().parse_args(["--bogus"])
    assert request.value.code == 2
