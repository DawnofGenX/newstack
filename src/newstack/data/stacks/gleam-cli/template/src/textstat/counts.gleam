import gleam/bit_array

/// The three figures `wc` reports: line count, word count and byte count.
pub type Counts {
  Counts(lines: Int, words: Int, bytes: Int)
}

/// Count lines, words and bytes in a raw byte buffer.
///
/// Lines follow `wc -l`: they count `0x0A` bytes, so a final line without a
/// trailing newline is not counted. Words are runs of non-whitespace bytes
/// (whitespace = space, tab, newline, vertical tab, form feed, carriage
/// return). Bytes are raw bytes, so UTF-8 text is counted by its encoded
/// width, not its codepoint count.
pub fn of_bytes(data: BitArray) -> Counts {
  Counts(
    lines: count_lines(data),
    words: count_words(data),
    bytes: bit_array.byte_size(data),
  )
}

/// Add two Counts, for the `total` row.
pub fn add(a: Counts, b: Counts) -> Counts {
  Counts(
    lines: a.lines + b.lines,
    words: a.words + b.words,
    bytes: a.bytes + b.bytes,
  )
}

/// The zero Counts, used as the fold identity for the `total` row.
pub fn zero() -> Counts {
  Counts(lines: 0, words: 0, bytes: 0)
}

fn count_lines(data: BitArray) -> Int {
  count_lines_helper(data, 0)
}

fn count_lines_helper(data: BitArray, acc: Int) -> Int {
  case data {
    <<>> -> acc
    <<b:8, rest:bits>> -> {
      let add = case b {
        10 -> 1
        _ -> 0
      }
      count_lines_helper(rest, acc + add)
    }
    _ -> acc
  }
}

fn is_space(b: Int) -> Bool {
  b == 32 || b == 9 || b == 10 || b == 11 || b == 12 || b == 13
}

fn count_words(data: BitArray) -> Int {
  count_words_helper(data, True, 0)
}

fn count_words_helper(data: BitArray, prev_space: Bool, acc: Int) -> Int {
  case data {
    <<>> -> acc
    <<b:8, rest:bits>> -> {
      let is_sp = is_space(b)
      let n = case is_sp {
        True -> 0
        False ->
          case prev_space {
            True -> 1
            False -> 0
          }
      }
      count_words_helper(rest, is_sp, acc + n)
    }
    _ -> acc
  }
}
