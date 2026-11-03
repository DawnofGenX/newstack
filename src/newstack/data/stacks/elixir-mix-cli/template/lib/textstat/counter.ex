defmodule Textstat.Counter do
  @moduledoc """
  Pure counting over a binary: no file access, no printing, no exit codes.

  Works on bytes rather than graphemes so that invalid UTF-8 in a real file is
  counted instead of raising, and so the byte total is exact.
  """

  alias Textstat.Counts

  # A newline is the only line separator (a lone carriage return is whitespace),
  # which matches how `wc -l` reads the same file.
  @whitespace [0x20, 0x09, 0x0D, 0x0B, 0x0C]

  @doc "Counts lines, words and bytes in *data*."
  @spec count(binary()) :: Counts.t()
  def count(data) when is_binary(data) do
    {lines, words} = scan(data, 0, 0, false)

    Counts.new(lines, words, byte_size(data))
  end

  defp scan(<<>>, lines, words, _in_word), do: {lines, words}

  defp scan(<<0x0A, rest::binary>>, lines, words, _in_word) do
    scan(rest, lines + 1, words, false)
  end

  defp scan(<<byte, rest::binary>>, lines, words, in_word) do
    cond do
      byte in @whitespace -> scan(rest, lines, words, false)
      in_word -> scan(rest, lines, words, true)
      true -> scan(rest, lines, words + 1, true)
    end
  end
end
