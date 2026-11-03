defmodule Textstat.CounterTest do
  use ExUnit.Case, async: true

  alias Textstat.{Counter, Counts}

  test "an empty input counts nothing" do
    assert Counter.count("") == Counts.new(0, 0, 0)
  end

  test "counts lines, words and bytes" do
    assert Counter.count("one two\nthree\n") == Counts.new(2, 3, 14)
  end

  test "a missing trailing newline is not a line" do
    assert Counter.count("one two") == Counts.new(0, 2, 7)
  end

  test "crlf endings count one line and keep the carriage return as a separator" do
    assert Counter.count("one\r\ntwo\r\n") == Counts.new(2, 2, 10)
  end

  test "bytes are counted, not characters" do
    assert Counter.count("héllo\n") == Counts.new(1, 1, 7)
  end

  test "blank lines are lines without words" do
    assert Counter.count("a\n\n\nb\n") == Counts.new(4, 2, 6)
  end

  test "invalid utf-8 is counted byte by byte instead of raising" do
    assert Counter.count(<<0xFF, 0xFE, ?\s, ?a>>) == Counts.new(0, 2, 4)
  end

  test "totals add up" do
    total = Counts.plus(Counts.new(1, 2, 3), Counts.new(4, 5, 6))

    assert total == Counts.new(5, 7, 9)
  end
end
