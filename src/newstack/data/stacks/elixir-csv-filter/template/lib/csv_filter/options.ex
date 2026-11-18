defmodule CsvFilter.Options do
  @moduledoc "Hand-rolled argv parsing for the CSV filter."

  @version "0.1.0"

  defstruct column: nil,
            value: nil,
            invert: false,
            header: true,
            files: [],
            status: :ok,
            error: nil

  @type t :: %__MODULE__{
          column: String.t() | nil,
          value: String.t() | nil,
          invert: boolean(),
          header: boolean(),
          files: [String.t()],
          status: :ok | :help | :version | :error,
          error: String.t() | nil
        }

  @spec version() :: String.t()
  def version, do: @version

  @spec parse([String.t()]) :: t()
  def parse(args) when is_list(args) do
    parse(args, %__MODULE__{}, false)
  end

  defp parse([], acc, _only_files) do
    cond do
      acc.status != :ok ->
        acc

      acc.column == nil or acc.value == nil ->
        %{acc | status: :error, error: "missing required option: --column and --value"}

      true ->
        acc
    end
  end

  defp parse(["-h" | _rest], acc, _only_files), do: %{acc | status: :help}
  defp parse(["--help" | _rest], acc, _only_files), do: %{acc | status: :help}
  defp parse(["-V" | _rest], acc, _only_files), do: %{acc | status: :version}
  defp parse(["--version" | _rest], acc, _only_files), do: %{acc | status: :version}

  defp parse(["-c", val | rest], acc, only_files) do
    parse(rest, %{acc | column: val}, only_files)
  end

  defp parse(["--column", val | rest], acc, only_files) do
    parse(rest, %{acc | column: val}, only_files)
  end

  defp parse(["--column=" <> val | rest], acc, only_files) do
    parse(rest, %{acc | column: val}, only_files)
  end

  defp parse(["-v", val | rest], acc, only_files) do
    parse(rest, %{acc | value: val}, only_files)
  end

  defp parse(["--value", val | rest], acc, only_files) do
    parse(rest, %{acc | value: val}, only_files)
  end

  defp parse(["--value=" <> val | rest], acc, only_files) do
    parse(rest, %{acc | value: val}, only_files)
  end

  defp parse(["--invert" | rest], acc, only_files) do
    parse(rest, %{acc | invert: true}, only_files)
  end

  defp parse(["--no-header" | rest], acc, only_files) do
    parse(rest, %{acc | header: false}, only_files)
  end

  defp parse(["--" | rest], acc, _only_files) do
    parse(rest, %{acc | files: acc.files ++ rest}, true)
  end

  defp parse([arg | rest], acc, only_files) do
    cond do
      only_files or not String.starts_with?(arg, "-") ->
        parse(rest, %{acc | files: acc.files ++ [arg]}, only_files)

      String.starts_with?(arg, "-") ->
        %{acc | status: :error, error: "unknown option '#{arg}'"}

      true ->
        parse(rest, %{acc | files: acc.files ++ [arg]}, only_files)
    end
  end

  @doc "Help text; the caller supplies the program name it was invoked as."
  @spec usage(String.t()) :: String.t()
  def usage(program) do
    """
    usage: #{program} --column COL --value VAL [--invert] [--no-header] [FILE ...]

    Filter CSV rows where COL equals VAL. COL may be a 1-based index or a
    header name. With no FILE, reads standard input.

      -c, --column COL   column to filter on
      -v, --value VAL    value to keep
          --invert       keep rows that do NOT match
          --no-header    treat the first row as data
      -h, --help         show this help and exit
      -V, --version      show the version and exit
    """
  end
end
