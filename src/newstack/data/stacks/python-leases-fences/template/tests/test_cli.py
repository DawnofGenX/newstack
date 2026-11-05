import io
from contextlib import redirect_stderr, redirect_stdout

import pytest

from {{ package_name }} import cli as subject


def run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = subject.main(argv)
    return code, out.getvalue(), err.getvalue()


def test_demo_exits_zero() -> None:
    code, out, _ = run(["demo"])
    assert code == subject.EXIT_OK
    assert "6. " in out


def test_model_exits_zero() -> None:
    code, out, _ = run(["model"])
    assert code == subject.EXIT_OK
    assert "contract" in out


def test_model_refuses_a_pause_inside_the_lease() -> None:
    code, _, err = run(["model", "--ttl-ms", "1000", "--pause-ms", "500"])
    assert code == subject.EXIT_UNUSABLE
    assert "never expires" in err


def test_model_refuses_a_zero_ttl() -> None:
    code, _, err = run(["model", "--ttl-ms", "0"])
    assert code == subject.EXIT_UNUSABLE
    assert "at least 1" in err


def test_selftest_exits_zero() -> None:
    code, out, _ = run(["selftest"])
    assert code == subject.EXIT_OK
    assert "checks passed" in out


def test_version_exits_zero() -> None:
    with pytest.raises(SystemExit) as raised:
        run(["--version"])
    assert raised.value.code == 0


def test_no_command_is_a_usage_error() -> None:
    with pytest.raises(SystemExit) as raised:
        run([])
    assert raised.value.code == 2
