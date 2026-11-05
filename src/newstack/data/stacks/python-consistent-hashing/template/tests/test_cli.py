import io
from contextlib import redirect_stderr, redirect_stdout

import pytest

from {{ package_name }} import cli as subject


def run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = subject.main(argv)
    return code, out.getvalue(), err.getvalue()


def test_map_prints_the_loads() -> None:
    code, out, _ = run(["map", "--nodes", "a,b,c", "--keys", "300"])
    assert code == subject.EXIT_OK
    assert "imbalance" in out
    assert out.count("a ") >= 1


def test_map_emits_json_when_asked() -> None:
    code, out, _ = run(["map", "--nodes", "a,b", "--keys", "50", "--json"])
    assert code == subject.EXIT_OK
    assert '"loads"' in out


def test_map_refuses_duplicate_nodes() -> None:
    code, _, err = run(["map", "--nodes", "a,a", "--keys", "10"])
    assert code == subject.EXIT_UNUSABLE
    assert "repeats" in err


def test_map_refuses_zero_keys() -> None:
    code, _, err = run(["map", "--nodes", "a", "--keys", "0"])
    assert code == subject.EXIT_UNUSABLE
    assert "at least 1" in err


def test_ring_names_the_owner() -> None:
    code, out, _ = run(["ring", "--nodes", "a,b,c", "--key", "user:00001"])
    assert code == subject.EXIT_OK
    assert "owner" in out


def test_ring_accepts_weights() -> None:
    code, out, _ = run(["ring", "--nodes", "a", "--key", "k", "--weights", "b=2"])
    assert code == subject.EXIT_OK
    assert "points" in out


def test_ring_refuses_a_malformed_weight() -> None:
    code, _, err = run(["ring", "--nodes", "a", "--key", "k", "--weights", "b=x"])
    assert code == subject.EXIT_UNUSABLE
    assert "name=count" in err


def test_move_reports_less_movement_than_modulo() -> None:
    code, out, _ = run(["move", "--nodes", "a,b,c", "--add", "d", "--keys", "3000"])
    assert code == subject.EXIT_OK
    moved = int(out.split("moved")[1].split()[0])
    assert moved < 3000 * 0.32
    assert "modulo" in out


def test_move_gates_on_the_limit() -> None:
    code, out, _ = run(
        ["move", "--nodes", "a,b,c", "--add", "d", "--keys", "2000", "--max-moved", "0.5"]
    )
    assert code == subject.EXIT_BREACH
    assert "FAIL" in out


def test_move_refuses_a_node_already_on_the_ring() -> None:
    code, _, err = run(["move", "--nodes", "a,b", "--add", "b", "--keys", "10"])
    assert code == subject.EXIT_UNUSABLE
    assert "already on the ring" in err


def test_move_can_show_the_moves() -> None:
    code, out, _ = run(["move", "--nodes", "a,b", "--add", "c", "--keys", "200", "--show", "3"])
    assert code == subject.EXIT_OK
    assert "->" in out


def test_balance_gates_on_the_split() -> None:
    code, out, _ = run(["balance", "--nodes", "a,b,c", "--keys", "400", "--max-imbalance", "1.0"])
    assert code == subject.EXIT_BREACH
    assert "gate        FAIL" in out


def test_balance_passes_when_the_split_is_even_enough() -> None:
    code, out, _ = run(["balance", "--nodes", "a,b,c", "--keys", "2000", "--max-imbalance", "2.0"])
    assert code == subject.EXIT_OK
    assert "ok" in out


def test_demo_prints_every_story() -> None:
    code, out, _ = run(["demo"])
    assert code == subject.EXIT_OK
    assert out.startswith("1. ")
    assert "6. " in out


def test_version_is_reported_by_argparse() -> None:
    with pytest.raises(SystemExit) as raised:
        run(["--version"])
    assert raised.value.code == 0


def test_a_missing_command_is_a_usage_error() -> None:
    with pytest.raises(SystemExit) as raised:
        run([])
    assert raised.value.code == 2


def test_unknown_flag_is_a_usage_error() -> None:
    with pytest.raises(SystemExit) as raised:
        run(["map", "--nope"])
    assert raised.value.code == 2
