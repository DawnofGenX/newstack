defmodule Textstat.Options do
  @moduledoc """
  Hand-rolled argv parsing, so every branch is a unit test and nothing depends
  on a parser library.

  Parsing never prints and never exits: it returns a struct whose `status` says
  what the caller should do next.
  """

  @version "0.1.0"

  defstruct mode: :all, files: [], status: :ok, error: nil

  @type mode :: :all | :lines | :words | :bytes
  @type status :: :ok | :help | :version | :error

  @type t :: %__MODULE__{
          mode: mode(),
          files: [String.t()],
          status: status(),
          error: String.t() | nil
        }

  @spec version() :: String.t()
  def version, do: @version

  @doc "Parses *args* into a `t:t/0`; flags stop being special after `--`."
  @spec parse([String.t()]) :: t()
  def parse(args) when is_list(args) do
    parse(args, %__MODULE__{}, nil, false)
  end

  defp parse([], acc, chosen, _only_files), do: %{acc | mode: chosen || :all}

  defp parse([arg | rest], acc, chosen, only_files) do
    case tag(arg, only_files) do
      :file ->
        parse(rest, %{acc | files: acc.files ++ [arg]}, chosen, only_files)

      :separator ->
        parse(rest, acc, chosen, true)

      :help ->
        %{acc | status: :help, mode: chosen || :all}

      :version ->
        %{acc | status: :version, mode: chosen || :all}

      {:mode, mode} when chosen == nil or chosen == mode ->
        parse(rest, acc, mode, only_files)

      {:mode, _mode} ->
        bad_usage(acc, chosen, "#{arg} conflicts with an earlier mode")

      :unknown ->
        bad_usage(acc, chosen, "unknown option '#{arg}'")
    end
  end

  defp bad_usage(acc, chosen, message) do
    %{acc | status: :error, mode: chosen || :all, error: message}
  end

  defp tag(_arg, true), do: :file
  defp tag("", _only_files), do: :file
  defp tag("-", _only_files), do: :file
  defp tag("--", _only_files), do: :separator
  defp tag(arg, _only_files) when arg in ["-h", "--help"], do: :help
  defp tag(arg, _only_files) when arg in ["-V", "--version"], do: :version
  defp tag(arg, _only_files) when arg in ["-l", "--lines"], do: {:mode, :lines}
  defp tag(arg, _only_files) when arg in ["-w", "--words"], do: {:mode, :words}
  defp tag(arg, _only_files) when arg in ["-c", "--bytes"], do: {:mode, :bytes}

  defp tag(arg, _only_files) do
    if String.starts_with?(arg, "-"), do: :unknown, else: :file
  end

  @doc "Help text; the caller supplies the program name it was invoked as."
  @spec usage(String.t()) :: String.t()
  def usage(program) do
    """
    usage: #{program} [-l | -w | -c] [--] [FILE ...]

    Count lines, words and bytes in each FILE, or in standard input
    when no FILE is given. With more than one FILE a total is printed.

      -l, --lines     print the line count only
      -w, --words     print the word count only
      -c, --bytes     print the byte count only
      -h, --help      show this help and exit
      -V, --version   show the version and exit
    """
  end
end
