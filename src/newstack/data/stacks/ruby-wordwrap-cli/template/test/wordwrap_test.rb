# frozen_string_literal: true

require 'minitest/autorun'

require_relative '../lib/wordwrap'

class WordwrapTest < Minitest::Test
  def test_a_line_that_already_fits_is_untouched
    assert_equal 'hello world', Wordwrap.wrap('hello world', width: 80)
  end

  def test_words_fill_a_line_greedily
    assert_equal "one two\nthree", Wordwrap.wrap('one two three', width: 7)
  end

  def test_a_word_exactly_at_the_width_is_kept_on_the_line
    assert_equal 'abc def', Wordwrap.wrap('abc def', width: 7)
  end

  def test_an_existing_paragraph_is_reflowed
    text = "one two\nthree"
    assert_equal 'one two three', Wordwrap.wrap(text, width: 80)
  end

  def test_blank_lines_separate_paragraphs
    text = "aaa bbb\n\nccc ddd"
    assert_equal "aaa bbb\n\nccc ddd", Wordwrap.wrap(text, width: 7)
  end

  def test_extra_spaces_collapse
    assert_equal 'one two', Wordwrap.wrap("  one\t\ttwo  ", width: 20)
  end

  def test_a_word_longer_than_the_width_is_not_split
    assert_equal "short\nunbreakable", Wordwrap.wrap('short unbreakable', width: 5)
  end

  def test_wrapping_is_idempotent
    text = 'the quick brown fox jumps over the lazy dog'
    once = Wordwrap.wrap(text, width: 12)
    assert_equal once, Wordwrap.wrap(once, width: 12)
  end

  def test_windows_line_endings_are_normalised
    assert_equal 'a b', Wordwrap.wrap("a\r\nb", width: 20)
  end

  def test_empty_text_stays_empty
    assert_equal '', Wordwrap.wrap('', width: 20)
  end

  def test_consecutive_blank_lines_collapse_to_one
    ## A paragraph break is a break; how many empty lines the author left is
    ## whitespace, and collapsing it keeps the output stable.
    assert_equal "a\n\nb", Wordwrap.wrap("a\n\n\nb", width: 20)
  end

  def test_width_must_be_positive
    assert_raises(Wordwrap::Error) { Wordwrap.wrap('a b', width: 0) }
    assert_raises(Wordwrap::Error) { Wordwrap.wrap('a b', width: -5) }
  end

  def test_the_default_width_is_76
    text = (['word'] * 40).join(' ')
    wrapped = Wordwrap.wrap(text)
    assert_operator wrapped.lines.map(&:chomp).map(&:length).max, :<=, 76
  end
end
