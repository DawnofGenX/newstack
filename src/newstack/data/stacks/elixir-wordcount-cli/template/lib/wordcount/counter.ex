defmodule WordCount.Counter do
  @moduledoc "Tokenising, frequency counting and rendering for the word count CLI."

  # A word is a run of letters or digits that may contain an internal apostrophe
  # or hyphen, so "don't" and "co-op" stay single words while "3.14" splits.
  @word ~r/[\p{L}\p{N}]+(?:['’\-][\p{L}\p{N}]+)*/u

  @type counts :: %{String.t() => pos_integer()}
  @type pair :: {String.t(), pos_integer()}
  @type options :: [
          ignore_case: boolean(),
          min_length: pos_integer(),
          stopwords: MapSet.t(String.t())
        ]

  @spec tokens(String.t()) :: [String.t()]
  def tokens(text) when is_binary(text) do
    @word |> Regex.scan(text) |> Enum.map(&hd/1)
  end

  @spec count([String.t()], options()) :: counts()
  def count(tokens, options \\ []) do
    ignore_case = Keyword.get(options, :ignore_case, false)
    min_length = Keyword.get(options, :min_length, 1)
    stopwords = Keyword.get(options, :stopwords, MapSet.new())

    tokens
    |> Enum.map(&normalise(&1, ignore_case))
    |> Enum.reject(&(String.length(&1) < min_length))
    |> Enum.reject(&MapSet.member?(stopwords, &1))
    |> Enum.frequencies()
  end

  @spec ranked(counts(), :freq | :alpha) :: [pair()]
  def ranked(counts, sort \\ :freq)

  def ranked(counts, :alpha) do
    counts |> Map.to_list() |> Enum.sort_by(fn {word, _count} -> word end)
  end

  def ranked(counts, :freq) do
    counts |> Map.to_list() |> Enum.sort_by(fn {word, count} -> {-count, word} end)
  end

  @spec select(counts(), non_neg_integer(), :freq | :alpha) :: [pair()]
  def select(counts, limit, sort \\ :freq) do
    pairs = ranked(counts, sort)

    if limit > 0 do
      Enum.take(pairs, limit)
    else
      pairs
    end
  end

  @spec stats(counts()) :: map()
  def stats(counts) do
    total = counts |> Map.values() |> Enum.sum()
    distinct = map_size(counts)

    longest =
      case Map.keys(counts) do
        [] -> ""
        words -> Enum.max_by(words, &String.length/1)
      end

    average =
      if distinct == 0 do
        0.0
      else
        lengths = counts |> Map.keys() |> Enum.map(&String.length/1)
        Float.round(Enum.sum(lengths) / distinct, 2)
      end

    %{total: total, distinct: distinct, longest: longest, average_length: average}
  end

  @spec format_pairs([pair()], :text | :tsv | :json) :: String.t()
  def format_pairs(pairs, format)

  def format_pairs(pairs, :json) do
    body =
      Enum.map_join(pairs, ",", fn {word, count} ->
        json_string(word) <> ":" <> Integer.to_string(count)
      end)

    "{" <> body <> "}"
  end

  def format_pairs(pairs, :tsv) do
    Enum.map_join(pairs, "\n", fn {word, count} -> word <> "\t" <> Integer.to_string(count) end)
  end

  def format_pairs(pairs, :text) do
    Enum.map_join(pairs, "\n", fn {word, count} -> word <> " " <> Integer.to_string(count) end)
  end

  @spec json_string(String.t()) :: String.t()
  def json_string(text) do
    escaped =
      text
      |> String.replace("\\", "\\\\")
      |> String.replace("\"", "\\\"")
      |> String.replace("\n", "\\n")
      |> String.replace("\t", "\\t")
      |> String.replace("\r", "\\r")

    "\"" <> escaped <> "\""
  end

  @spec stopwords(String.t()) :: MapSet.t(String.t())
  def stopwords(text) do
    text
    |> String.split(["\n", "\r\n", ","])
    |> Enum.map(&String.trim/1)
    |> Enum.reject(&(&1 == "" or String.starts_with?(&1, "#")))
    |> Enum.map(&String.downcase/1)
    |> MapSet.new()
  end

  defp normalise(word, true), do: String.downcase(word)
  defp normalise(word, false), do: word
end
