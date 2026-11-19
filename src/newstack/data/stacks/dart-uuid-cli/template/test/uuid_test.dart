import 'package:test/test.dart';
import 'package:{{ package_name }}/{{ package_name }}.dart';

void main() {
  group('generate', () {
    test('v4 matches canonical form', () {
      final u = Uuid.v4();
      expect(Uuid.isValid(u), isTrue);
      expect(Uuid.versionOf(u), 4);
    });
    test('v7 matches canonical form', () {
      final u = Uuid.v7();
      expect(Uuid.isValid(u), isTrue);
      expect(Uuid.versionOf(u), 7);
    });
    test('generated values differ', () {
      expect(Uuid.v4(), isNot(Uuid.v4()));
    });
    test('v7 carries a recent timestamp', () {
      final before = DateTime.now().millisecondsSinceEpoch;
      final u = Uuid.v7();
      final ts = Uuid.timestampMillis(u)!;
      final after = DateTime.now().millisecondsSinceEpoch;
      expect(ts, greaterThanOrEqualTo(before - 5));
      expect(ts, lessThanOrEqualTo(after + 5));
    });
  });

  group('validate', () {
    test('accepts a valid v4', () {
      expect(Uuid.isValid('550e8400-e29b-41d4-a716-446655440000'), isTrue);
    });
    test('rejects bad length', () {
      expect(Uuid.isValid('550e8400-e29b-41d4-a716'), isFalse);
    });
    test('rejects bad variant', () {
      expect(Uuid.isValid('550e8400-e29b-41d4-0716-446655440000'), isFalse);
    });
    test('rejects non-hex', () {
      expect(Uuid.isValid('zzzzzzzz-e29b-41d4-a716-446655440000'), isFalse);
    });
    test('versionOf null for invalid', () {
      expect(Uuid.versionOf('nope'), isNull);
    });
  });

  group('parse', () {
    test('timestampMillis null for v4', () {
      expect(Uuid.timestampMillis(Uuid.v4()), isNull);
    });
    test('timestampMillis reads embedded ms', () {
      final ms = 1700000000000;
      final u = Uuid.v7(DateTime.fromMillisecondsSinceEpoch(ms, isUtc: true));
      expect(Uuid.timestampMillis(u), ms);
    });
  });

  group('sort', () {
    test('sorts lexicographically', () {
      // use uuids
      final u1 = '00000000-0000-4000-8000-000000000001';
      final u2 = '00000000-0000-4000-8000-000000000002';
      final u3 = '00000000-0000-4000-8000-000000000000';
      expect(Uuid.sort([u2, u1, u3]), [u3, u1, u2]);
    });
    test('sort does not mutate input', () {
      final input = ['00000000-0000-4000-8000-000000000002', '00000000-0000-4000-8000-000000000001'];
      Uuid.sort(input);
      expect(input.first, '00000000-0000-4000-8000-000000000002');
    });
  });
}
