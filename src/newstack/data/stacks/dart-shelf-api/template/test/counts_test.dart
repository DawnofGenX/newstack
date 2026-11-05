import "package:test/test.dart";
import "package:{{ package_name }}/{{ package_name }}.dart";

void main() {
  group("countText", () {
    final cases = <List<Object>>[
      <Object>["one line", "hello world\n", const Counts(lines: 1, words: 2, bytes: 12)],
      <Object>["empty", "", const Counts(lines: 0, words: 0, bytes: 0)],
      <Object>["blank lines", "\n\nx\n", const Counts(lines: 3, words: 1, bytes: 4)],
      <Object>["whitespace only", "  \t ", const Counts(lines: 0, words: 0, bytes: 4)],
      <Object>["no trailing newline", "abc", const Counts(lines: 0, words: 1, bytes: 3)],
      <Object>["utf8", "héllo wörld\n", const Counts(lines: 1, words: 2, bytes: 14)],
      <Object>["emoji", "🙂\n", const Counts(lines: 1, words: 1, bytes: 5)],
    ];

    for (final testCase in cases) {
      test(testCase[0] as String, () {
        expect(countText(testCase[1] as String), testCase[2] as Counts);
      });
    }
  });

  test("countsJson carries the text and the three counts", () {
    expect(countsJson("a b\n", const Counts(lines: 1, words: 2, bytes: 4)), <String, Object?>{
      "text": "a b\n",
      "lines": 1,
      "words": 2,
      "bytes": 4,
    });
  });
}
