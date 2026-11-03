import 'dart:convert';

import 'counts.dart';

/// Counting logic, with no file system and no printing.
///
/// The caller reads the bytes and prints the result, which is what keeps this
/// library directly testable.
abstract final class TextStat {
  /// One match per word: a run of characters that are not whitespace.
  static final RegExp _word = RegExp(r'\S+', unicode: true);

  static final RegExp _newline = RegExp('\n');

  /// Counts [bytes], decoding them as UTF-8. Malformed input is replaced rather
  /// than rejected, so the byte count still matches the file on disk.
  static Counts count(List<int> bytes) {
    final text = utf8.decode(bytes, allowMalformed: true);
    return Counts(
      lines: _newline.allMatches(text).length,
      words: _word.allMatches(text).length,
      bytes: bytes.length,
    );
  }

  /// Convenience for callers that already hold text.
  static Counts countText(String text) => count(utf8.encode(text));
}
