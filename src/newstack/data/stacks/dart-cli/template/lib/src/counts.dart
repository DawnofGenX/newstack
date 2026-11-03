/// Line, word and byte totals for one input.
///
/// Value type: two totals with the same numbers are equal, so tests can compare
/// against a literal instead of unpacking fields.
final class Counts {
  const Counts({
    required this.lines,
    required this.words,
    required this.bytes,
  });

  /// An all-zero total, the seed for summing several files.
  static const Counts zero = Counts(lines: 0, words: 0, bytes: 0);

  /// Newline characters seen in the input.
  final int lines;

  /// Runs of non-whitespace characters.
  final int words;

  /// Raw bytes, which is what `wc -c` reports for UTF-8 text.
  final int bytes;

  /// Adds two totals so several files can be reported as one.
  Counts operator +(Counts other) => Counts(
        lines: lines + other.lines,
        words: words + other.words,
        bytes: bytes + other.bytes,
      );

  @override
  bool operator ==(Object other) =>
      other is Counts &&
      other.lines == lines &&
      other.words == words &&
      other.bytes == bytes;

  @override
  int get hashCode => Object.hash(lines, words, bytes);

  @override
  String toString() => 'Counts(lines: $lines, words: $words, bytes: $bytes)';
}
