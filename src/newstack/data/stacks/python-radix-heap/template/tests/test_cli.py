from __future__ import annotations

import subprocess
import sys

from {{ package_name }}.cli import main

CODEX = "fixtures/keys.txt"


def test_build_prints_where_the_keys_sit(capsys) -> None:
    assert main(["build", "--count", "32"]) == 0
    printed = capsys.readouterr().out
    assert "size 32" in printed
    assert "buckets hold keys" in printed


def test_pop_answers_in_order(capsys) -> None:
    assert main(["pop", "--keys", CODEX, "3"]) == 0
    printed = capsys.readouterr().out.splitlines()
    assert "popped   '0' = 0 base 0" in printed[0]
    assert "popped   '15' = 2 base 15" in printed[2]


def test_popping_past_the_heap_reports_it(capsys) -> None:
    assert main(["pop", "--keys", CODEX, "99"]) == 1
    assert "drained  empty" in capsys.readouterr().out


def test_push_names_the_bucket_the_key_took(capsys) -> None:
    assert main(["push", "30"]) == 0
    printed = capsys.readouterr().out
    assert "pushed       30  push bucket 5 rebuilt=False" in printed


def test_a_push_onto_a_loaded_heap_names_the_seat(capsys) -> None:
    assert main(["push", "--keys", CODEX, "7"]) == 0
    printed = capsys.readouterr().out
    assert "rebuilt=False" in printed
    assert "push bucket 3" in printed


def test_a_key_below_the_floor_is_unusable(capsys) -> None:
    assert main(["push", "-5"]) == 2
    assert "no key" in capsys.readouterr().out


def test_a_missing_file_is_unusable(capsys) -> None:
    assert main(["build", "--keys", "nowhere.txt"]) == 2
    assert "cannot read" in capsys.readouterr().err


def test_the_stories_hold_through_the_cli(capsys) -> None:
    assert main(["demo"]) == 0
    assert "6 of 6 hold" in capsys.readouterr().out


def test_the_selftest_runs_through_the_cli(capsys) -> None:
    assert main(["selftest"]) == 0
    assert "0 failed" in capsys.readouterr().out


def test_the_package_runs_as_a_module() -> None:
    done = subprocess.run(
        [sys.executable, "-m", "{{ package_name }}", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0
    assert "0.1.0" in done.stdout
