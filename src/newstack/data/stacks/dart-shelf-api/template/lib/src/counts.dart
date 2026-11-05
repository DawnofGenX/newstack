import "dart:convert";

/// Line, word and byte counts for one piece of text.
///
/// The rules match `wc`: a line ends at `\n`, a word is a maximal run of non-space
/// characters, and bytes are the UTF-8 encoding length (which is why `héllo` is five
/// characters but six bytes).
class Counts {
  const Counts({required this.lines, required this.words, required this.bytes});

  final int lines;
  final int words;
  final int bytes;

  @override
  String toString() => "Counts(lines: $lines, words: $words, bytes: $bytes)";

  @override
  bool operator ==(Object other) =>
      other is Counts &&
      other.lines == lines &&
      other.words == words &&
      other.bytes == bytes;

  @override
  int get hashCode => Object.hash(lines, words, bytes);
}

/// Counts [text] the way `wc` does.
Counts countText(String text) => Counts(
  lines: "\n".allMatches(text).length,
  words: RegExp(r"\S+").allMatches(text).length,
  bytes: utf8.encode(text).length,
);

/// The JSON shape every response uses.
Map<String, Object?> countsJson(String text, Counts counts) => <String, Object?>{
  "text": text,
  "lines": counts.lines,
  "words": counts.words,
  "bytes": counts.bytes,
};
