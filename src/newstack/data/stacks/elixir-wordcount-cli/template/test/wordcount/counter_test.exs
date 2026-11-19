defmodule WordCount.CounterTest do
  use ExUnit.Case, async: true

  alias WordCount.Counter

  describe "tokens/1" do
    test "splits on punctuation and keeps internal apostrophes and hyphens" do
      assert Counter.tokens("Hello, world! It's fine.") == ["Hello", "world", "It's", "fine"]
      assert Counter.tokens("a co-op day") == ["a", "co-op", "day"]
    end

    test "a full stop is a separator, not part of a number" do
      assert Counter.tokens("pi is 3.14 today") == ["pi", "is", "3", "14", "today"]
    end

    test "unicode letters are words" do
      assert Counter.tokens("naïve café Über") == ["naïve", "café", "Über"]
    end

    test "an empty document has no words" do
      assert Counter.tokens("") == []
      assert Counter.tokens("   \n\t ") == []
    end
  end

  describe "count/2" do
    test "counts exact words" do
      tokens = Counter.tokens("a b b c c c")
      assert Counter.count(tokens) == %{"a" => 1, "b" => 2, "c" => 3}
    end

    test "folds case when asked and keeps it otherwise" do
      tokens = Counter.tokens("The the the")
      assert Counter.count(tokens) == %{"The" => 1, "the" => 2}
      assert Counter.count(tokens, ignore_case: true) == %{"the" => 3}
    end

    test "drops words shorter than the minimum length" do
      tokens = Counter.tokens("a bb ccc")
      assert Counter.count(tokens, min_length: 2) == %{"bb" => 1, "ccc" => 1}
    end

    test "drops stopwords after case folding" do
      tokens = Counter.tokens("The cat and the hat")
      stopwords = Counter.stopwords("the\nand\n# a comment\n")

      assert Counter.count(tokens, ignore_case: true, stopwords: stopwords) == %{
               "cat" => 1,
               "hat" => 1
             }
    end
  end

  describe "ranking" do
    test "frequent words come first and ties break alphabetically" do
      counts = Counter.count(Counter.tokens("b a c c"))
      assert Counter.ranked(counts) == [{"c", 2}, {"a", 1}, {"b", 1}]
    end

    test "alphabetical ranking ignores counts" do
      counts = Counter.count(Counter.tokens("b a c c"))
      assert Counter.ranked(counts, :alpha) == [{"a", 1}, {"b", 1}, {"c", 2}]
    end

    test "select/3 takes the head of the ranking, and 0 means everything" do
      counts = Counter.count(Counter.tokens("a b b c c c"))
      assert Counter.select(counts, 2) == [{"c", 3}, {"b", 2}]
      assert Counter.select(counts, 0) == [{"c", 3}, {"b", 2}, {"a", 1}]
      assert Counter.select(counts, 2, :alpha) == [{"a", 1}, {"b", 2}]
    end
  end

  describe "stats/1" do
    test "summarises the counts" do
      counts = Counter.count(Counter.tokens("aa bbb bbb cccc cccc cccc"))

      assert Counter.stats(counts) == %{
               total: 6,
               distinct: 3,
               longest: "cccc",
               average_length: 3.0
             }
    end

    test "an empty document has zero stats" do
      assert Counter.stats(%{}) == %{total: 0, distinct: 0, longest: "", average_length: 0.0}
    end
  end

  describe "format_pairs/2" do
    test "text, tsv and json output" do
      pairs = [{"b", 2}, {"a", 1}]
      assert Counter.format_pairs(pairs, :text) == "b 2\na 1"
      assert Counter.format_pairs(pairs, :tsv) == "b\t2\na\t1"
      assert Counter.format_pairs(pairs, :json) == ~s({"b":2,"a":1})
    end

    test "json escapes quotes and backslashes" do
      assert Counter.format_pairs([{~s(a"b\\c), 1}], :json) == ~s({"a\\"b\\\\c":1})
    end
  end

  describe "stopwords/1" do
    test "reads one word per line, skips blanks and comments" do
      stopwords = Counter.stopwords("the\n\n  AND  \n# comment\nof,to\n")
      assert MapSet.to_list(stopwords) |> Enum.sort() == ["and", "of", "the", "to"]
    end
  end
end
