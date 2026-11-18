defmodule CsvFilter.CLI do
  @moduledoc "Runnable command: argv in, exit code back."

  alias CsvFilter.{Filter, Options}

  @program "{{ npm_name }}"

  @type io_map :: %{
          read_stdin: (-> {:ok, binary()} | {:error, term()}),
          read_file: (String.t() -> {:ok, binary()} | {:error, term()}),
          out: (String.t() -> any()),
          err: (String.t() -> any())
        }

  @spec main([String.t()]) :: no_return()
  def main(argv) do
    System.halt(run(argv, system_io()))
  end

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

      %Options{column: column, value: value, invert: invert, header: header, files: []} ->
        case io.read_stdin.() do
          {:ok, data} ->
            io.out.(Filter.filter(data, column, value, invert, header))
            0

          {:error, reason} ->
            io.err.("error: cannot read standard input: #{format_reason(reason)}\n")
            1
        end

      %Options{column: column, value: value, invert: invert, header: header, files: files} ->
        {failed?} =
          Enum.reduce(files, {false}, fn path, {failed?} ->
            case read(path, io) do
              {:ok, data} ->
                io.out.(Filter.filter(data, column, value, invert, header))
                {failed?}

              {:error, :stdin, reason} ->
                io.err.("error: cannot read standard input: #{format_reason(reason)}\n")
                {true}

              {:error, reason} ->
                io.err.("error: cannot open '#{path}': #{format_reason(reason)}\n")
                {true}
            end
          end)

        if failed?, do: 1, else: 0
    end
  end

  defp read("-", io) do
    case io.read_stdin.() do
      {:ok, data} -> {:ok, data}
      {:error, reason} -> {:error, :stdin, reason}
    end
  end

  defp read(path, io), do: io.read_file.(path)

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
