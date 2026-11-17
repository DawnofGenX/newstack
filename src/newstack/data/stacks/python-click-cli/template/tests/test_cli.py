from click.testing import CliRunner

from {{ package_name }}.cli import cli


def test_greet():
    runner = CliRunner()
    result = runner.invoke(cli, ["greet", "--name", "ada"])
    assert result.exit_code == 0
    assert "hello ada" in result.output


def test_count():
    runner = CliRunner()
    result = runner.invoke(cli, ["count", "one two three"])
    assert result.exit_code == 0
    assert "words=3" in result.output
