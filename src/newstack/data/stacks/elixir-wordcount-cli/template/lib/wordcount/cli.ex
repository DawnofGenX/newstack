defmodule WordCount.CLI do
  @moduledoc "Runnable command: argv in, exit code back."

  alias WordCount.{Counter, Options}

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

      %Options{} = options ->
        report(options, io)
    end
  end

  defp report(options, io) do
    with {:ok, stopwords} <- load_stopwords(options, io),
         {:ok, texts} <- read_inputs(options, io) do
      tokens = Enum.flat_map(texts, &Counter.tokens/1)

      counts =
        Counter.count(tokens,
          ignore_case: options.ignore_case,
          min_length: options.min_length,
          stopwords: stopwords
        )

      emit(counts, options, io)
      0
    else
      {:error, code} -> code
    end
  end

  defp emit(counts, %Options{total_only: true}, io) do
    counts |> Map.values() |> Enum.sum() |> Integer.to_string() |> then(&io.out.(&1 <> "\n"))
  end

  defp emit(counts, %Options{unique: true}, io) do
    words = counts |> Counter.ranked(:alpha) |> Enum.map(fn {word, _count} -> word end)

    case words do
      [] -> io.out.("")
      _ -> io.out.(Enum.join(words, "\n") <> "\n")
    end
  end

  defp emit(counts, %Options{} = options, io) do
    pairs = Counter.select(counts, options.top, options.sort)

    case pairs do
      [] -> io.out.("")
      _ -> io.out.(Counter.format_pairs(pairs, options.format) <> "\n")
    end
  end

  defp load_stopwords(%Options{stopwords: nil}, _io), do: {:ok, MapSet.new()}

  defp load_stopwords(%Options{stopwords: path}, io) do
    case io.read_file.(path) do
      {:ok, data} ->
        {:ok, Counter.stopwords(data)}

      {:error, reason} ->
        io.err.("error: cannot read stopwords '#{path}': #{format_reason(reason)}\n")
        {:error, 1}
    end
  end

  defp read_inputs(%Options{files: []}, io) do
    case io.read_stdin.() do
      {:ok, data} -> {:ok, [data]}
      {:error, reason} -> read_failure("standard input", reason, io)
    end
  end

  defp read_inputs(%Options{files: files}, io) do
    Enum.reduce_while(files, {:ok, []}, fn path, {:ok, acc} ->
      case read_one(path, io) do
        {:ok, data} -> {:cont, {:ok, acc ++ [data]}}
        {:error, label, reason} -> {:halt, read_failure(label, reason, io)}
      end
    end)
  end

  defp read_one("-", io) do
    case io.read_stdin.() do
      {:ok, data} -> {:ok, data}
      {:error, reason} -> {:error, "standard input", reason}
    end
  end

  defp read_one(path, io) do
    case io.read_file.(path) do
      {:ok, data} -> {:ok, data}
      {:error, reason} -> {:error, "'#{path}'", reason}
    end
  end

  defp read_failure(label, reason, io) do
    io.err.("error: cannot read #{label}: #{format_reason(reason)}\n")
    {:error, 1}
  end

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
