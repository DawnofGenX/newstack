# frozen_string_literal: true

module Textstat
  # The six ASCII separators wc uses. Ruby's \s is ASCII-only, but spelling the set
  # out keeps the rule visible and keeps it identical in every port of this contract.
  SEPARATORS = "[ \t\n\r\v\f]+"

  # One immutable value object: `Data` gives readers, `==`, and freezing for free,
  # so a test can compare whole results instead of three separate numbers.
  Counts = Data.define(:lines, :words, :bytes) do
    def to_h = { lines:, words:, bytes: }

    def to_json = %({"lines":#{lines},"words":#{words},"bytes":#{bytes}})
  end

  module_function

  # Lines are newline bytes (a trailing newline does not open an empty line),
  # words are runs of non-separator bytes, bytes are the UTF-8 length.
  def count(text)
    Counts.new(text.count("\n"), words_in(text), text.bytesize)
  end

  def words_in(text)
    text.split(/#{SEPARATORS}/).reject(&:empty?).size
  end
end
