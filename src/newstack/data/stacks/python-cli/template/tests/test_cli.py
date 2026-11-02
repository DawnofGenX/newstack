from {{ package_name }}.cli import main


def test_greet_uses_default_name(capsys) -> None:
    assert main(["greet"]) == 0
    assert capsys.readouterr().out.strip() == "Hello, world!"


def test_greet_uses_given_name(capsys) -> None:
    assert main(["greet", "--name", "Ada"]) == 0
    assert "Ada" in capsys.readouterr().out


def test_version_prints_and_exits(capsys) -> None:
    import pytest

    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert "0.1.0" in capsys.readouterr().out
