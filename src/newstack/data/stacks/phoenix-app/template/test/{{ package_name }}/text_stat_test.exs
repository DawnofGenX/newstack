defmodule {{ class_name }}.TextStatTest do
  use ExUnit.Case, async: true

  alias {{ class_name }}.TextStat

  test "counts text the way wc does" do
    cases = [
      {"", %{lines: 0, words: 0, bytes: 0}},
      {"one two\n", %{lines: 1, words: 2, bytes: 8}},
      {"one two\nthree\n", %{lines: 2, words: 3, bytes: 14}},
      {"  padded  \n", %{lines: 1, words: 1, bytes: 11}},
      {"no trailing newline", %{lines: 0, words: 3, bytes: 19}},
      {"héllo wörld\n", %{lines: 1, words: 2, bytes: 14}}
    ]

    for {text, expected} <- cases do
      assert TextStat.of(text) == expected, "counting #{inspect(text)}"
    end
  end

  test "blank lines are lines" do
    assert TextStat.of("\n\nx\n") == %{lines: 3, words: 1, bytes: 4}
  end

  test "whitespace only text has no words but keeps its bytes" do
    assert TextStat.of("  \t ") == %{lines: 0, words: 0, bytes: 4}
  end

  test "rejects a non-binary instead of guessing" do
    assert_raise FunctionClauseError, fn -> TextStat.of(:nope) end
  end
end
