package {{ package_name }}

final case class Counts(lines: Int, words: Int, bytes: Int)

object Counts:
  /** A line is a newline byte, a word a maximal run of non-space characters. */
  def of(text: String): Counts =
    var lines = 0
    var words = 0
    var inWord = false
    var i = 0
    while i < text.length do
      val c = text.charAt(i)
      if c == '\n' then lines += 1
      if c.isWhitespace then inWord = false
      else if !inWord then
        inWord = true
        words += 1
      i += 1
    Counts(lines, words, text.getBytes("UTF-8").length)
