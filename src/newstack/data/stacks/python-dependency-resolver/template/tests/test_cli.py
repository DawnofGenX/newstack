import json

import pytest

from {{ package_name }} import cli


def run(capsys, argv):
    code = cli.main(argv)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_resolve_prints_one_line_per_package(capsys):
    code, out, _ = run(capsys, ["resolve", "--root", "web=^2.0.0", "--root", "cli=^1.0.0"])
    assert code == cli.EXIT_OK
    assert "web                2.0.0" in out
    assert "resolved 3 package(s)" in out


def test_a_conflict_exits_one_and_prints_no_version(capsys):
    code, out, err = run(capsys, ["resolve", "--root", "web=^2.1.0", "--root", "cli=^1.0.0"])
    assert code == cli.EXIT_UNSATISFIED
    assert out == ""
    assert "no resolution exists" in err
    assert "shared" in err


def test_an_unreadable_range_is_unusable_input(capsys):
    code, _, err = run(capsys, ["resolve", "--root", "web=banana"])
    assert code == cli.EXIT_UNUSABLE
    assert "banana" in err


def test_a_malformed_root_is_refused_before_any_work(capsys):
    code, _, err = run(capsys, ["resolve", "--root", "web"])
    assert code == cli.EXIT_UNUSABLE
    assert "name=RANGE" in err


def test_no_root_at_all_is_refused(capsys):
    code, _, err = run(capsys, ["resolve"])
    assert code == cli.EXIT_UNUSABLE
    assert "at least one --root" in err


def test_why_names_the_requirements(capsys):
    code, out, _ = run(capsys, ["why", "--root", "web=^2.0.0", "--root", "cli=^1.0.0", "shared"])
    assert code == cli.EXIT_OK
    assert "shared 1.4.0" in out
    assert "web@2.0.0 needs shared ^1.2.0" in out


def test_why_refuses_a_package_that_is_not_in_the_resolution(capsys):
    code, _, err = run(capsys, ["why", "--root", "web=^2.0.0", "tiny"])
    assert code == cli.EXIT_UNUSABLE
    assert "not in this resolution" in err


def test_write_lock_then_check_is_clean(capsys, tmp_path):
    lock = tmp_path / "deps.lock.json"
    code, out, _ = run(
        capsys,
        ["resolve", "--root", "web=^2.0.0", "--root", "cli=^1.0.0", "--write-lock", str(lock)],
    )
    assert code == cli.EXIT_OK
    assert lock.exists()
    payload = json.loads(lock.read_text())
    assert payload["packages"]["web"] == "2.0.0"

    code, out, _ = run(
        capsys, ["check", "--root", "web=^2.0.0", "--root", "cli=^1.0.0", "--lock", str(lock)]
    )
    assert code == cli.EXIT_OK
    assert "still resolves" in out


def test_check_fails_when_the_lock_no_longer_fits_the_roots(capsys, tmp_path):
    lock = tmp_path / "deps.lock.json"
    run(capsys, ["resolve", "--root", "web=^2.0.0", "--write-lock", str(lock)])
    code, out, _ = run(capsys, ["check", "--root", "shared=^2.0.0", "--lock", str(lock)])
    assert code == cli.EXIT_UNSATISFIED
    assert "drift(s)" in out


def test_json_output_is_the_same_answer(capsys):
    code, out, _ = run(capsys, ["resolve", "--root", "web=^2.0.0", "--json"])
    assert code == cli.EXIT_OK
    payload = json.loads(out)
    assert payload["packages"]["web"] == "2.1.1"
    assert payload["explored"] >= 1


def test_a_missing_lockfile_is_unusable_input(capsys, tmp_path):
    code, _, err = run(
        capsys, ["check", "--root", "web=^2.0.0", "--lock", str(tmp_path / "nope.json")]
    )
    assert code == cli.EXIT_UNUSABLE
    assert "no lockfile at" in err


def test_demo_and_selftest_exit_zero(capsys):
    assert cli.main(["demo"]) == 0
    assert cli.main(["selftest"]) == 0
    capsys.readouterr()


@pytest.mark.parametrize("command", ["demo", "selftest"])
def test_demo_and_selftest_print_something(capsys, command):
    code = cli.main([command])
    out = capsys.readouterr().out
    assert code == 0
    assert out.strip()
