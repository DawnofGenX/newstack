defmodule Textstat.CLITest do
  use ExUnit.Case, async: true

  alias Textstat.CLI

  defp io(files, stdin \\ "") do
    %{
      read_stdin: fn -> {:ok, stdin} end,
      read_file: fn path ->
        case Map.fetch(files, path) do
          {:ok, data} -> {:ok, data}
          :error -> {:error, :enoent}
        end
      end,
      out: fn text -> send(self(), {:out, text}) end,
      err: fn text -> send(self(), {:err, text}) end
    }
  end

  test "--help prints usage and exits 0" do
    assert CLI.run(["--help"], io(%{})) == 0
    assert_received {:out, text}
    assert text =~ "usage: "
    assert text =~ "-l, --lines"
  end

  test "--version prints the version and exits 0" do
    assert CLI.run(["--version"], io(%{})) == 0
    assert_received {:out, "0.1.0\n"}
  end

  test "an unknown flag prints an error and exits 2" do
    assert CLI.run(["--bogus"], io(%{})) == 2
    assert_received {:err, text}
    assert text =~ "error: unknown option '--bogus'"
    assert_received {:err, usage}
    assert usage =~ "usage: "
  end

  test "a missing file reports it and exits 1" do
    assert CLI.run(["missing.txt"], io(%{})) == 1
    assert_received {:err, message}
    assert message =~ "error: cannot open 'missing.txt'"
  end

  test "standard input is counted when no file is given" do
    assert CLI.run([], io(%{}, "one two\nthree\n")) == 0
    assert_received {:out, "       2       3      14\n"}
  end

  test "one file prints its name, two files add a total" do
    files = %{"a.txt" => "one two\n", "b.txt" => "three\n"}

    assert CLI.run(["-w", "a.txt", "b.txt"], io(files)) == 0
    assert_received {:out, "       2 a.txt\n"}
    assert_received {:out, "       1 b.txt\n"}
    assert_received {:out, "       3 total\n"}
  end

  test "a bad file among good ones still exits 1" do
    files = %{"a.txt" => "one\n"}

    assert CLI.run(["a.txt", "gone.txt"], io(files)) == 1
    assert_received {:out, "       1       1       4 a.txt\n"}
    assert_received {:err, message}
    assert message =~ "error: cannot open 'gone.txt'"
  end
end
