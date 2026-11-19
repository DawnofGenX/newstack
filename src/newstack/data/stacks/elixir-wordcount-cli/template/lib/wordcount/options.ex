defmodule WordCount.Options do
  @moduledoc "Hand-rolled argv parsing for the word count CLI."

  @version "0.1.0"

  defstruct top: 10,
            min_length: 1,
            ignore_case: false,
            stopwords: nil,
            sort: :freq,
            format: :text,
            unique: false,
            total_only: false,
            files: [],
            status: :ok,
            error: nil

  @type t :: %__MODULE__{
          top: non_neg_integer(),
          min_length: pos_integer(),
          ignore_case: boolean(),
          stopwords: String.t() | nil,
          sort: :freq | :alpha,
          format: :text | :tsv | :json,
          unique: boolean(),
          total_only: boolean(),
          files: [String.t()],
          status: :ok | :help | :version | :error,
          error: String.t() | nil
        }

  @spec version() :: String.t()
  def version, do: @version

  @spec usage(String.t()) :: String.t()
  def usage(program) do
    """
    usage: #{program} [options] [file ...]

    Count word frequencies across the given files, or standard input.

    options:
      -n, --top N          show the N most frequent words (0 = every word, default 10)
      -m, --min-length N   ignore words shorter than N characters (default 1)
      -i, --ignore-case    fold case before counting
      -s, --stopwords FILE drop words listed in FILE (one per line, # comments)
          --sort MODE      freq (default) or alpha
          --tsv            tab separated output instead of "word count"
          --json           JSON object of word to count
      -u, --unique         print the distinct words only, no counts
      -t, --total          print the total number of counted words only
      -h, --help           show this message
          --version        show the version
      --                   treat every remaining argument as a file
    """
  end

  @spec parse([String.t()]) :: t()
  def parse(args) when is_list(args), do: parse(args, %__MODULE__{}, false)

  defp parse([], acc, _only_files), do: acc

  defp parse([arg | rest], acc, only_files) do
    cond do
      only_files ->
        parse(rest, %{acc | files: acc.files ++ [arg]}, true)

      arg == "--" ->
        parse(rest, acc, true)

      arg == "-" ->
        parse(rest, %{acc | files: acc.files ++ ["-"]}, false)

      not String.starts_with?(arg, "-") ->
        parse(rest, %{acc | files: acc.files ++ [arg]}, false)

      true ->
        parse_option(arg, rest, acc, only_files)
    end
  end

  defp parse_option(flag, _rest, acc, _only_files) when flag in ["-h", "--help"],
    do: %{acc | status: :help}

  defp parse_option("--version", _rest, acc, _only_files), do: %{acc | status: :version}

  defp parse_option(flag, rest, acc, only_files) when flag in ["-i", "--ignore-case"],
    do: parse(rest, %{acc | ignore_case: true}, only_files)

  defp parse_option(flag, rest, acc, only_files) when flag in ["-u", "--unique"],
    do: parse(rest, %{acc | unique: true}, only_files)

  defp parse_option(flag, rest, acc, only_files) when flag in ["-t", "--total"],
    do: parse(rest, %{acc | total_only: true}, only_files)

  defp parse_option("--json", rest, acc, only_files),
    do: parse(rest, %{acc | format: :json}, only_files)

  defp parse_option("--tsv", rest, acc, only_files),
    do: parse(rest, %{acc | format: :tsv}, only_files)

  defp parse_option(flag, rest, acc, only_files) when flag in ["-n", "--top"] do
    case take_integer(flag, rest) do
      {:ok, value, remaining} when value >= 0 ->
        parse(remaining, %{acc | top: value}, only_files)

      {:ok, _value, _remaining} ->
        error(acc, "invalid value for #{flag}: must be zero or more")

      {:error, message} ->
        error(acc, message)
    end
  end

  defp parse_option(flag, rest, acc, only_files) when flag in ["-m", "--min-length"] do
    case take_integer(flag, rest) do
      {:ok, value, remaining} when value >= 1 ->
        parse(remaining, %{acc | min_length: value}, only_files)

      {:ok, _value, _remaining} ->
        error(acc, "invalid value for #{flag}: must be one or more")

      {:error, message} ->
        error(acc, message)
    end
  end

  defp parse_option(flag, rest, acc, only_files) when flag in ["-s", "--stopwords"] do
    case rest do
      [path | remaining] -> parse(remaining, %{acc | stopwords: path}, only_files)
      [] -> error(acc, "missing value for #{flag}")
    end
  end

  defp parse_option("--sort", [mode | remaining], acc, only_files) do
    case mode do
      "freq" -> parse(remaining, %{acc | sort: :freq}, only_files)
      "alpha" -> parse(remaining, %{acc | sort: :alpha}, only_files)
      other -> error(acc, "unknown sort mode: #{other} (expected freq or alpha)")
    end
  end

  defp parse_option("--sort", [], acc, _only_files), do: error(acc, "missing value for --sort")

  defp parse_option(flag, _rest, acc, _only_files), do: error(acc, "unknown option: #{flag}")

  defp error(acc, message), do: %{acc | status: :error, error: message}

  defp take_integer(flag, [value | remaining]) do
    case Integer.parse(value) do
      {number, ""} -> {:ok, number, remaining}
      _ -> {:error, "invalid value for #{flag}: #{value}"}
    end
  end

  defp take_integer(flag, []), do: {:error, "missing value for #{flag}"}
end
