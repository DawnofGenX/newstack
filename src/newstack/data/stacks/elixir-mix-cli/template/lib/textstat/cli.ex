defmodule Textstat.CLI do
  @moduledoc """
  The runnable command: argv in, figures out, an exit code back.

  Every device is passed in as a function map, so tests drive `run/2` with fake
  input and output. `main/1` is the only place that builds real devices and the
  only place that halts.

  Exit codes: `0` success, `1` unreadable input, `2` bad usage.
  """

  alias Textstat.{Counter, Counts, Options}

  @program "{{ npm_name }}"

  @type io_map :: %{
          read_stdin: (() -> {:ok, binary()} | {:error, term()}),
          read_file: (String.t() -> {:ok, binary()} | {:error, term()}),
          out: (String.t() -> any()),
          err: (String.t() -> any())
        }

  @doc "Escript entry point: runs and halts with the resulting exit code."
  @spec main([String.t()]) :: no_return()
  def main(argv) do
    System.halt(run(argv, system_io()))
  end

  @doc "Runs one command line against *io*, returning the exit code."
  @spec run([String.t()], io_map()) :: non_neg_integer()
  def run(argv, io) do
    case Options.parse(argv) do
      %Options{status: :help} ->
        io.out.(Options.usage(@program))
        0

      %Options{status: :version} ->
        io.out.(Options.version() <> "\n")
        0

      %Options{status: :error, error: message} ->
        io.err.("error: " <> message <> "\n\n")
        io.err.(Options.usage(@program))
        2

      %Options{mode: mode, files: files} ->
        count_all(mode, files, io)
    end
  end

  defp count_all(mode, [], io) do
    case io.read_stdin.() do
      {:ok, data} ->
        print(io, mode, Counter.count(data), "")
        0

      {:error, reason} ->
        io.err.("error: cannot read standard input: #{format_reason(reason)}\n")
        1
    end
  end

  defp count_all(mode, files, io) do
    {total, failed?} =
      Enum.reduce(files, {Counts.new(0, 0, 0), false}, fn path, {total, failed?} ->
        case read(path, io) do
          {:ok, data} ->
            counts = Counter.count(data)
            print(io, mode, counts, label(path))
            {Counts.plus(total, counts), failed?}

          {:error, :stdin, reason} ->
            io.err.("error: cannot read standard input: #{format_reason(reason)}\n")
            {total, true}

          {:error, reason} ->
            io.err.("error: cannot open '#{path}': #{format_reason(reason)}\n")
            {total, true}
        end
      end)

    if length(files) > 1, do: print(io, mode, total, "total")

    if failed?, do: 1, else: 0
  end

  defp read("-", io) do
    case io.read_stdin.() do
      {:ok, data} -> {:ok, data}
      {:error, reason} -> {:error, :stdin, reason}
    end
  end

  defp read(path, io), do: io.read_file.(path)

  defp label("-"), do: ""
  defp label(path), do: path

  defp print(io, mode, %Counts{} = counts, label) do
    figures =
      for {selected?, value} <- [
            {mode in [:all, :lines], counts.lines},
            {mode in [:all, :words], counts.words},
            {mode in [:all, :bytes], counts.bytes}
          ],
          selected?,
          do: value |> Integer.to_string() |> String.pad_leading(8)

    io.out.(Enum.join(figures) <> suffix(label) <> "\n")
  end

  defp suffix(""), do: ""
  defp suffix(label), do: " " <> label

  defp format_reason(reason) when is_atom(reason), do: to_string(:file.format_error(reason))
  defp format_reason(reason), do: to_string(reason)

  defp system_io do
    %{
      read_stdin: fn -> read_stdin() end,
      read_file: fn path -> File.read(path) end,
      out: fn text -> IO.write(text) end,
      err: fn text -> IO.write(:stderr, text) end
    }
  end

  defp read_stdin do
    case IO.binread(:stdio, :eof) do
      :eof -> {:ok, ""}
      {:error, reason} -> {:error, reason}
      data when is_binary(data) -> {:ok, data}
    end
  end
end
