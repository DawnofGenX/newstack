package textstat

/** Which figures to print. `wc` prints all three when given no flag. */
final case class Figures(lines: Boolean, words: Boolean, bytes: Boolean)

object Figures:
  val all: Figures = Figures(lines = true, words = true, bytes = true)
  val none: Figures = Figures(lines = false, words = false, bytes = false)

/** A `wc`-style tally: line feeds, maximal runs of non-whitespace, raw bytes. */
final case class Counts(lines: Long, words: Long, bytes: Long):
  def add(other: Counts): Counts =
    Counts(lines + other.lines, words + other.words, bytes + other.bytes)

  /** The printed columns, in `wc` order, for the figures that were asked for. */
  def columns(figures: Figures): List[Long] =
    List(
      Option.when(figures.lines)(lines),
      Option.when(figures.words)(words),
      Option.when(figures.bytes)(bytes)
    ).flatten

object Counts:
  val empty: Counts = Counts(0L, 0L, 0L)

  private def isSpace(b: Byte): Boolean =
    b == ' '.toByte || b == '\t'.toByte || b == '\n'.toByte ||
      b == '\r'.toByte || b == 11.toByte || b == 12.toByte

  /**
   * Count raw bytes, so the numbers match `wc -l -w -c` on the same file:
   * a line is a `\n` byte (a last line without a trailing newline is not
   * counted), a word is a maximal run of non-whitespace bytes, and bytes are
   * bytes, not characters.
   */
  def ofBytes(data: Array[Byte]): Counts =
    var lines = 0L
    var words = 0L
    var inWord = false
    var i = 0
    while i < data.length do
      val b = data(i)
      if b == '\n'.toByte then lines += 1
      if isSpace(b) then inWord = false
      else if !inWord then
        words += 1
        inWord = true
      i += 1
    Counts(lines, words, data.length.toLong)

  /** The column width `wc` uses: the widest figure printed anywhere in the output. */
  def width(rows: Seq[Counts], figures: Figures): Int =
    rows.flatMap(_.columns(figures)).map(_.toString.length).maxOption.getOrElse(0)

  /** Right-align every column to `width`, the way `wc` lines up its output. */
  def formatRow(figures: Figures, counts: Counts, label: String, width: Int): String =
    val cells = counts.columns(figures)
    val numbers = cells.map(cell => " " * (width - cell.toString.length) + cell)
    (numbers :+ label).mkString(" ")
