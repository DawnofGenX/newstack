defmodule CsvFilter.OptionsTest do
  use ExUnit.Case, async: true

  alias CsvFilter.Options

  test "parses column and value" do
    opts = Options.parse(["-c", "1", "-v", "alice"])
    assert opts.status == :ok
    assert opts.column == "1"
    assert opts.value == "alice"
    assert opts.files == []
  end

  test "unknown option is error" do
    opts = Options.parse(["--bogus"])
    assert opts.status == :error
  end

  test "help stops parsing" do
    assert Options.parse(["--help"]).status == :help
  end

  test "version" do
    assert Options.parse(["-V"]).status == :version
  end

  test "missing required options" do
    opts = Options.parse(["file.csv"])
    assert opts.status == :error
  end

  test "usage names program" do
    assert Options.usage("prog") =~ "usage: prog"
  end
end
