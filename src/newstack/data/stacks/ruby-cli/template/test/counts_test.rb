# frozen_string_literal: true

require_relative "test_helper"

class CountsTest < Minitest::Test
  def test_empty_input_is_all_zero
    assert_equal Textstat::Counts.new(0, 0, 0), Textstat.count("")
  end

  def test_a_trailing_newline_does_not_open_an_empty_line
    assert_equal Textstat::Counts.new(1, 2, 4), Textstat.count("a b\n")
  end

  def test_text_without_a_newline_has_no_complete_line
    # wc counts newline bytes, so "hi" is one word and zero lines.
    assert_equal Textstat::Counts.new(0, 1, 2), Textstat.count("hi")
  end

  def test_utf8_counts_bytes_not_characters
    # "héllo wörld" is 11 characters and 13 bytes.
    assert_equal Textstat::Counts.new(1, 2, 14), Textstat.count("héllo wörld\n")
  end

  def test_every_wc_separator_splits_a_word
    assert_equal 7, Textstat.count("a b\tc\nd\re\vf\fg").words
  end

  def test_runs_of_separators_do_not_make_empty_words
    assert_equal 2, Textstat.count("  a \t\n b  ").words
  end

  def test_counts_is_immutable_and_comparable
    counts = Textstat.count("a b\n")
    assert counts.frozen?
    assert_equal({ lines: 1, words: 2, bytes: 4 }, counts.to_h)
  end
end
