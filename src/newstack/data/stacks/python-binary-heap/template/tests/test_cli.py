from __future__ import annotations

import json

from {{ package_name }}.cli import (
    EXIT_OK,
    EXIT_UNUSABLE,
    main,
)


def test_version_and_help_exit_zero() -> None:
    assert main(["--version"]) == 0
    assert main(["--help"]) == 0


def test_len_counts_the_fixture_style_list(tmp_path) -> None:
    keys = tmp_path / "keys.txt"
    keys.write_text("5\n-2\n5\n", encoding="utf-8")
    assert main(["len", "--keys", str(keys)]) == EXIT_OK
    assert main(["len", "--keys", str(keys), "--json"]) == EXIT_OK


def test_peek_names_the_minimum(tmp_path, capsys) -> None:
    keys = tmp_path / "keys.txt"
    keys.write_text("5\n-2\n5\n", encoding="utf-8")
    assert main(["peek", "--keys", str(keys)]) == EXIT_OK
    assert "head       -2" in capsys.readouterr().out


def test_a_push_seats_a_key(tmp_path, capsys) -> None:
    keys = tmp_path / "keys.txt"
    keys.write_text("5\n", encoding="utf-8")
    assert main(["push", "--keys", str(keys), "-9"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "keys       2" in out
    assert "head       -9" in out


def test_a_pop_hands_over_the_minimum(tmp_path, capsys) -> None:
    keys = tmp_path / "keys.txt"
    keys.write_text("5\n-2\n", encoding="utf-8")
    assert main(["pop", "--keys", str(keys)]) == EXIT_OK
    assert "popped     -2" in capsys.readouterr().out


def test_pop_hands_over_the_smallest_and_refills_quietly(tmp_path, capsys) -> None:
    keys = tmp_path / "keys.txt"
    keys.write_text("5\n-2\n", encoding="utf-8")
    # the file is re-read each run, so a second pop sees the full list again
    assert main(["pop", "--keys", str(keys)]) == EXIT_OK
    assert "popped     -2" in capsys.readouterr().out


def test_an_empty_key_list_is_unusable(tmp_path) -> None:
    keys = tmp_path / "empty.txt"
    keys.write_text("# nothing\n", encoding="utf-8")
    assert main(["pop", "--keys", str(keys)]) == EXIT_UNUSABLE
    assert main(["peek", "--keys", str(keys)]) == EXIT_UNUSABLE


def test_json_answers_carry_the_array(tmp_path, capsys) -> None:
    keys = tmp_path / "keys.txt"
    keys.write_text("5\n-2\n5\n", encoding="utf-8")
    assert main(["peek", "--keys", str(keys), "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["keys"] == 3
    assert payload["head"] == -2
    assert sorted(payload["array"]) == [-2, 5, 5]


def test_a_missing_key_list_is_unusable(tmp_path) -> None:
    assert main(["len", "--keys", str(tmp_path / "missing.txt")]) == EXIT_UNUSABLE


def test_the_selftest_and_demo_answer_from_the_cli(capsys) -> None:
    assert main(["selftest"]) == EXIT_OK
    assert "0 failed" in capsys.readouterr().out
    assert main(["demo"]) == EXIT_OK
    assert "6 of 6 hold" in capsys.readouterr().out


def test_unknown_command_exits_two() -> None:
    assert main(["nonsense"]) == EXIT_UNUSABLE
