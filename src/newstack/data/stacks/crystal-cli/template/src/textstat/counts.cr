# Line, word and byte counting — the only place that decides an answer.
#
# Pure: no files, no stdout, no globals. The CLI reads bytes and prints them;
# this module just counts, so specs drive it directly.
module Textstat
  struct Counts
    getter lines : Int32
    getter words : Int32
    getter bytes : Int32

    def initialize(@lines : Int32 = 0, @words : Int32 = 0, @bytes : Int32 = 0)
    end

    # Counts `text` with `wc` semantics: `\n` is the only line separator, so
    # a last line without one is not a line; words are runs of non-whitespace
    # bytes; bytes are raw bytes, not characters.
    def self.of(text : String) : Counts
      lines = 0
      words = 0
      in_word = false

      text.each_byte do |byte|
        case byte
        when 0x0A_u8 # \n
          lines += 1
          in_word = false
        when 0x20_u8, 0x09_u8, 0x0D_u8, 0x0B_u8, 0x0C_u8 # space, \t, \r, \v, \f
          in_word = false
        else
          unless in_word
            words += 1
            in_word = true
          end
        end
      end

      Counts.new(lines, words, text.bytesize)
    end

    # Adds two totals so several files can be reported as one.
    def +(other : Counts) : Counts
      Counts.new(lines + other.lines, words + other.words, bytes + other.bytes)
    end

    def to_s(io : IO) : Nil
      io << "Counts(lines: " << lines << ", words: " << words << ", bytes: " << bytes << ")"
    end
  end
end
