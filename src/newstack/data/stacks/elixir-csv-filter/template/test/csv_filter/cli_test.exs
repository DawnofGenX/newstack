defmodule CsvFilter.CLITest do
  use ExUnit.Case, async: true

  alias CsvFilter.CLI

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
  end

  test "--version prints the version and exits 0" do
    assert CLI.run(["--version"], io(%{})) == 0
    assert_received {:out, "0.1.0\n"}
  end

  test "an unknown flag prints an error and exits 2" do
    assert CLI.run(["--bogus"], io(%{})) == 2
    assert_received {:err, text}
    assert text =~ "error: unknown option '--bogus'"
  end

  test "a missing file reports it and exits 1" do
    assert CLI.run(["-c", "1", "-v", "alice", "missing.txt"], io(%{})) == 1
    assert_received {:err, message}
    assert message =~ "error: cannot open 'missing.txt'"
  end

  test "stdin is filtered" do
    assert CLI.run(["-c", "1", "-v", "alice"], io(%{}, "name,age\nalice,30\nbob,25\n")) == 0
    assert_received {:out, "name,age\nalice,30\n"}
  end
end
