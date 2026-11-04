# frozen_string_literal: true

require "test_helper"

class TextStatTest < ActiveSupport::TestCase
  test "counts an empty string" do
    assert_equal({ lines: 0, words: 0, bytes: 0 }, TextStat.count(""))
  end

  test "counts lines, words and bytes" do
    assert_equal({ lines: 2, words: 3, bytes: 17 }, TextStat.count("alpha beta\ngamma\n"))
  end

  test "a final line without a newline still has words" do
    assert_equal({ lines: 0, words: 3, bytes: 19 }, TextStat.count("no trailing newline"))
  end

  test "counts bytes, not characters" do
    assert_equal({ lines: 1, words: 2, bytes: 14 }, TextStat.count("h\u00e9llo w\u00f6rld\n"))
  end

  test "treats every C whitespace byte as a separator" do
    assert_equal({ lines: 1, words: 4, bytes: 8 }, TextStat.count("a\tb\vc\fd\n"))
  end
end
