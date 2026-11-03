import 'dart:convert';

import 'package:{{ package_name }}/{{ package_name }}.dart';
import 'package:test/test.dart';

void main() {
  group('TextStat.count', () {
    test('counts an empty input as all zeros', () {
      expect(
        TextStat.count(const <int>[]),
        const Counts(lines: 0, words: 0, bytes: 0),
      );
    });

    test('counts lines, words and bytes', () {
      final bytes = utf8.encode('one two\nthree\n');
      expect(
        TextStat.count(bytes),
        const Counts(lines: 2, words: 3, bytes: 14),
      );
    });

    test('counts a last line with no trailing newline', () {
      expect(
        TextStat.countText('one\ntwo'),
        const Counts(lines: 1, words: 2, bytes: 7),
      );
    });

    test('counts bytes rather than characters for non-ASCII text', () {
      expect(
        TextStat.countText('café'),
        const Counts(lines: 0, words: 1, bytes: 5),
      );
    });

    test('treats tabs and repeated spaces as separators', () {
      expect(
        TextStat.countText('\t a  b \n'),
        const Counts(lines: 1, words: 2, bytes: 8),
      );
    });
  });

  test('Counts adds up, which is how several files become one total', () {
    const first = Counts(lines: 1, words: 2, bytes: 3);
    const second = Counts(lines: 4, words: 5, bytes: 6);
    expect(first + second, const Counts(lines: 5, words: 7, bytes: 9));
    expect(first + Counts.zero, first);
  });
}
