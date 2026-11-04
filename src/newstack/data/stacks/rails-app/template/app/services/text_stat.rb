# frozen_string_literal: true

# Counts what wc counts: lines, words and bytes.
#
# The logic is deliberately independent of Rails: give it a string and it
# returns the three figures.  Everything that touches the request lives in the
# controller, which keeps this class cheap to test and easy to reuse.
class TextStat
  WHITESPACE = [" ", "\t", "\n", "\v", "\f", "\r"].freeze

  # @param text [String] already-decoded text
  # @return [Hash{Symbol=>Integer}] line, word and byte counts
  def self.count(text)
    lines = text.count("\n")
    words = 0
    in_word = false

    text.each_char do |char|
      if WHITESPACE.include?(char)
        in_word = false
      elsif !in_word
        in_word = true
        words += 1
      end
    end

    { lines: lines, words: words, bytes: text.bytesize }
  end
end
