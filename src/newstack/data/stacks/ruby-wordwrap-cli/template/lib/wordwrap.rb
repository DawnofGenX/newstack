# frozen_string_literal: true

# Greedy word wrapping that treats a blank line as a paragraph break.
#
# Two behaviours are worth pinning down, because every wrapping bug comes from
# one of them: existing single newlines inside a paragraph are treated as plain
# spaces (so a reflow is idempotent), and a word longer than the width is left
# alone rather than chopped — a broken URL is worse than a long line.
module Wordwrap
  DEFAULT_WIDTH = 76

  # Raised for a width the user could have typed: zero, negative, or not a
  # number at all.
  class Error < StandardError; end

  module_function

  def wrap(text, width: DEFAULT_WIDTH)
    raise Error, 'width must be a positive number' unless width.is_a?(Integer) && width.positive?

    paragraphs = text.gsub("\r\n", "\n").split(/\n[ \t]*\n/, -1)
    paragraphs.map { |paragraph| reflow(paragraph, width) }.join("\n\n")
  end

  # One paragraph: collapse every run of whitespace to a single space, then fill
  # lines greedily.
  def reflow(paragraph, width)
    words = paragraph.split(/\s+/).reject(&:empty?)
    return '' if words.empty?

    lines = []
    current = +''
    words.each do |word|
      if current.empty?
        current = +word
      elsif current.length + 1 + word.length <= width
        current << ' ' << word
      else
        lines << current
        current = +word
      end
    end
    lines << current unless current.empty?
    lines.join("\n")
  end
end
