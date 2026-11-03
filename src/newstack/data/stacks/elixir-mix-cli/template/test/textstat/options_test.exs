defmodule Textstat.OptionsTest do
  use ExUnit.Case, async: true

  alias Textstat.Options

  test "no arguments means every figure from standard input" do
    options = Options.parse([])

    assert options.status == :ok
    assert options.mode == :all
    assert options.files == []
    assert options.error == nil
  end

  test "each numeric flag selects one figure" do
    assert Options.parse(["-l"]).mode == :lines
    assert Options.parse(["--words"]).mode == :words
    assert Options.parse(["-c"]).mode == :bytes
  end

  test "repeating the same flag is fine" do
    assert Options.parse(["-l", "--lines"]).status == :ok
  end

  test "conflicting flags are a usage error" do
    options = Options.parse(["-l", "-w"])

    assert options.status == :error
    assert options.error =~ "conflicts with an earlier mode"
    assert options.error =~ "-w"
  end

  test "an unknown flag is a usage error" do
    options = Options.parse(["--bogus"])

    assert options.status == :error
    assert options.error == "unknown option '--bogus'"
  end

  test "help and version stop parsing" do
    assert Options.parse(["--help", "--bogus"]).status == :help
    assert Options.parse(["-V"]).status == :version
  end

  test "a bare dash and paths are files" do
    options = Options.parse(["-l", "-", "notes.txt"])

    assert options.mode == :lines
    assert options.files == ["-", "notes.txt"]
  end

  test "a double dash ends flag parsing" do
    options = Options.parse(["--", "-l"])

    assert options.status == :ok
    assert options.mode == :all
    assert options.files == ["-l"]
  end

  test "the usage text names the program" do
    assert Options.usage("textstat-sample") =~ "usage: textstat-sample [-l | -w | -c]"
    assert Options.usage("textstat-sample") =~ "-V, --version"
  end
end
