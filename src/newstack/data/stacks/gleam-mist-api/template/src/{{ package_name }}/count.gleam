import gleam/list
import gleam/string

pub type Counts {
  Counts(lines: Int, words: Int, bytes: Int)
}

fn is_space(char: String) -> Bool {
  char == " "
  || char == "\t"
  || char == "\n"
  || char == "\r"
  || char == "\u{000b}"
  || char == "\u{000c}"
}

fn step(state: #(Int, Int, Bool), char: String) -> #(Int, Int, Bool) {
  let #(lines, words, in_word) = state
  let lines = case char == "\n" {
    True -> lines + 1
    False -> lines
  }
  case is_space(char) {
    True -> #(lines, words, False)
    False ->
      case in_word {
        True -> #(lines, words, True)
        False -> #(lines, words + 1, True)
      }
  }
}

/// A line is a newline byte, a word is a maximal run of non-space characters and
/// `bytes` is the UTF-8 byte size (Gleam's `string.length` counts graphemes).
pub fn count_text(text: String) -> Counts {
  let #(lines, words, _) =
    text
    |> string.to_graphemes
    |> list.fold(#(0, 0, False), step)
  Counts(lines: lines, words: words, bytes: string.byte_size(text))
}
