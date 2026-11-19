defmodule WordCount.CLITest do
  use ExUnit.Case, async: true

  alias WordCount.CLI

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
    assert text =~ "usage: {{ npm_name }}"
  end

  test "--version prints the version and exits 0" do
    assert CLI.run(["--version"], io(%{})) == 0
    assert_received {:out, "0.1.0\n"}
  end

  test "an unknown option prints to stderr and exits 2" do
    assert CLI.run(["--bogus"], io(%{})) == 2
    assert_received {:err, text}
    assert text =~ "error: unknown option: --bogus"
  end

  test "a missing file exits 1 and names the file" do
    assert CLI.run(["gone.txt"], io(%{})) == 1
    assert_received {:err, text}
    assert text =~ "cannot read 'gone.txt'"
  end

  test "a missing stopwords file exits 1" do
    assert CLI.run(["--stopwords", "stop.txt"], io(%{})) == 1
    assert_received {:err, text}
    assert text =~ "cannot read stopwords 'stop.txt'"
  end

  test "counts standard input when no file is given" do
    assert CLI.run([], io(%{}, "a b b c\n")) == 0
    assert_received {:out, text}
    assert text == "b 2\na 1\nc 1\n"
  end

  test "honours --top and --sort" do
    assert CLI.run(~w(-n 1), io(%{}, "a b b c c c\n")) == 0
    assert_received {:out, "c 3\n"}

    assert CLI.run(["--top", "0", "--sort", "alpha"], io(%{}, "b a\n")) == 0
    assert_received {:out, "a 1\nb 1\n"}
  end

  test "--json renders an object and --tsv a table" do
    assert CLI.run(["--json", "--top", "1"], io(%{}, "a b b\n")) == 0
    assert_received {:out, ~s({"b":2}\n)}

    assert CLI.run(["--tsv"], io(%{}, "a a\n")) == 0
    assert_received {:out, "a\t2\n"}
  end

  test "--total prints the number of counted words" do
    assert CLI.run(["--total"], io(%{}, "a b b c c c\n")) == 0
    assert_received {:out, "6\n"}
  end

  test "--unique prints the distinct words alphabetically" do
    assert CLI.run(["--unique"], io(%{}, "b a b\n")) == 0
    assert_received {:out, "a\nb\n"}
  end

  test "several files are counted together and stdin comes from -" do
    files = %{"one.txt" => "apple banana\n", "two.txt" => "banana cherry\n"}
    assert CLI.run(["-n", "1", "one.txt", "two.txt"], io(files)) == 0
    assert_received {:out, "banana 2\n"}

    assert CLI.run(["-t", "-"], io(files, "cherry cherry\n")) == 0
    assert_received {:out, "2\n"}
  end
end
