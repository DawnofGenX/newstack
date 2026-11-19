defmodule WordCount.OptionsTest do
  use ExUnit.Case, async: true

  alias WordCount.Options

  test "defaults" do
    options = Options.parse([])
    assert options.status == :ok
    assert options.top == 10
    assert options.min_length == 1
    assert options.sort == :freq
    assert options.format == :text
    refute options.ignore_case
    refute options.unique
    refute options.total_only
    assert options.files == []
  end

  test "flags and values" do
    options = Options.parse(~w(-n 3 -m 4 -i -s words.txt --sort alpha --json notes.txt -))

    assert options.status == :ok
    assert options.top == 3
    assert options.min_length == 4
    assert options.ignore_case
    assert options.stopwords == "words.txt"
    assert options.sort == :alpha
    assert options.format == :json
    assert options.files == ["notes.txt", "-"]
  end

  test "--help and --version win over everything after them" do
    assert Options.parse(["--help"]).status == :help
    assert Options.parse(["-h"]).status == :help
    assert Options.parse(["--version"]).status == :version
  end

  test "a negative or non numeric --top is an error" do
    assert Options.parse(["--top", "-1"]).status == :error
    assert Options.parse(["--top"]).status == :error
    assert Options.parse(["-n", "many"]).status == :error
    assert Options.parse(["-n", "many"]).error =~ "invalid value for -n: many"
  end

  test "--top 0 means every word and is accepted" do
    assert Options.parse(["--top", "0"]).top == 0
  end

  test "--min-length rejects zero" do
    result = Options.parse(["--min-length", "0"])
    assert result.status == :error
    assert result.error =~ "must be one or more"
  end

  test "an unknown option is an error naming the flag" do
    result = Options.parse(["--bogus"])
    assert result.status == :error
    assert result.error == "unknown option: --bogus"
  end

  test "an unknown sort mode is an error" do
    result = Options.parse(["--sort", "length"])
    assert result.status == :error
    assert result.error =~ "unknown sort mode: length"
  end

  test "everything after -- is a file, even if it starts with a dash" do
    options = Options.parse(~w(-- -n --json))
    assert options.status == :ok
    assert options.files == ["-n", "--json"]
    assert options.top == 10
  end

  test "usage mentions the program name and the main flags" do
    text = Options.usage("count")
    assert text =~ "usage: count"
    assert text =~ "--top"
    assert text =~ "--stopwords"
  end
end
