import 'package:test/test.dart';
import 'package:{{ package_name }}/{{ package_name }}.dart';

void main() {
  group('canonicalize', () {
    test('sorts object keys by code unit', () {
      expect(canonicalize({'b': 1, 'a': 2, 'C': 3}), '{"C":3,"a":2,"b":1}');
    });

    test('sorts nested objects too', () {
      final value = {
        'outer': {'z': 1, 'a': {'y': 2, 'b': 3}},
        'list': [
          {'n': 1, 'm': 2},
        ],
      };
      expect(
        canonicalize(value),
        '{"list":[{"m":2,"n":1}],"outer":{"a":{"b":3,"y":2},"z":1}}',
      );
    });

    test('drops every insignificant space', () {
      expect(canonicalize([1, 2, 3]), '[1,2,3]');
      expect(canonicalize({}), '{}');
      expect(canonicalize([]), '[]');
    });

    test('writes whole doubles without a fraction', () {
      expect(canonicalize(2.0), '2');
      expect(canonicalize(2.5), '2.5');
      expect(canonicalize(-0.0), '0');
      expect(canonicalize(1e21), '1e+21');
    });

    test('escapes quotes, backslashes and control characters', () {
      expect(canonicalize('quote " and \\ slash'), r'"quote \" and \\ slash"');
      expect(canonicalize('tab\there'), r'"tab\there"');
      expect(canonicalize('\u0001'), r'"\u0001"');
      expect(canonicalize('line\nbreak'), r'"line\nbreak"');
    });

    test('keeps non-ASCII text readable', () {
      expect(canonicalize('café'), '"café"');
    });

    test('refuses NaN and infinity', () {
      expect(() => canonicalize(double.nan), throwsA(isA<CanonicalError>()));
      expect(() => canonicalize(double.infinity), throwsA(isA<CanonicalError>()));
    });

    test('refuses non-string object keys', () {
      expect(() => canonicalize({1: 'one'}), throwsA(isA<CanonicalError>()));
    });

    test('refuses values JSON cannot hold', () {
      expect(() => canonicalize(DateTime(2024)), throwsA(isA<CanonicalError>()));
    });
  });

  group('canonicalizeText', () {
    test('reorders keys from a document', () {
      expect(canonicalizeText('{"b": 1, "a": [2, 3]}'), '{"a":[2,3],"b":1}');
    });

    test('is idempotent', () {
      final once = canonicalizeText('{"z":1,"a":{"y":2,"x":3}}');
      expect(canonicalizeText(once), once);
    });

    test('reports malformed input', () {
      expect(
        () => canonicalizeText('{"a": }'),
        throwsA(isA<CanonicalError>().having((error) => error.message, 'message', contains('invalid JSON'))),
      );
    });
  });

  group('pretty', () {
    test('indents two spaces and keeps sorted keys', () {
      expect(
        pretty('{"b":1,"a":[1,2]}'),
        '{\n  "a": [\n    1,\n    2\n  ],\n  "b": 1\n}',
      );
    });
  });
}
