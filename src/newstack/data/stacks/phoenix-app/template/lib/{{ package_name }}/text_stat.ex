defmodule {{ class_name }}.TextStat do
  @moduledoc """
  Counts text the way `wc` does: newlines for lines, runs of whitespace-separated
  tokens for words, and bytes of the UTF-8 encoding for bytes.

  Pure: no I/O, no framework types, so the endpoint stays a thin serializer and
  these rules can be tested directly.
  """

  @type counts :: %{lines: non_neg_integer(), words: non_neg_integer(), bytes: non_neg_integer()}

  @doc """
  Counts `text`.

      iex> {{ class_name }}.TextStat.of("one two\\nthree\\n")
      %{lines: 2, words: 3, bytes: 14}
  """
  @spec of(binary()) :: counts()
  def of(text) when is_binary(text) do
    %{
      lines: length(String.split(text, "\n")) - 1,
      words: text |> String.split(~r/\s+/, trim: true) |> length(),
      bytes: byte_size(text)
    }
  end
end
