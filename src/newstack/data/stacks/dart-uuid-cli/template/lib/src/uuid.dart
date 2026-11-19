import 'dart:math';
import 'dart:typed_data';

/// RFC 9562 UUID helpers: generate, validate, inspect and order UUIDs.
class Uuid {
  static final Random _random = Random.secure();

  /// Generates a version 4 (random) UUID in canonical lowercase form.
  static String v4() {
    final bytes = Uint8List(16);
    for (var i = 0; i < 16; i++) {
      bytes[i] = _random.nextInt(256);
    }
    bytes[6] = (bytes[6] & 0x0f) | 0x40; // version 4
    bytes[8] = (bytes[8] & 0x3f) | 0x80; // variant 10
    return _format(bytes);
  }

  /// Generates a version 7 (time-ordered) UUID using the current time.
  static String v7([DateTime? now]) {
    final ms = (now ?? DateTime.now().toUtc()).millisecondsSinceEpoch;
    final bytes = Uint8List(16);
    // 48-bit Unix timestamp in milliseconds, big-endian.
    bytes[0] = (ms >> 40) & 0xff;
    bytes[1] = (ms >> 32) & 0xff;
    bytes[2] = (ms >> 24) & 0xff;
    bytes[3] = (ms >> 16) & 0xff;
    bytes[4] = (ms >> 8) & 0xff;
    bytes[5] = ms & 0xff;
    for (var i = 6; i < 16; i++) {
      bytes[i] = _random.nextInt(256);
    }
    bytes[6] = (bytes[6] & 0x0f) | 0x70; // version 7
    bytes[8] = (bytes[8] & 0x3f) | 0x80; // variant 10
    return _format(bytes);
  }

  static String _format(Uint8List b) {
    String hex(int v) => v.toRadixString(16).padLeft(2, '0');
    final parts = <String>[
      '${hex(b[0])}${hex(b[1])}${hex(b[2])}${hex(b[3])}',
      '${hex(b[4])}${hex(b[5])}',
      '${hex(b[6])}${hex(b[7])}',
      '${hex(b[8])}${hex(b[9])}',
      '${hex(b[10])}${hex(b[11])}${hex(b[12])}${hex(b[13])}${hex(b[14])}${hex(b[15])}',
    ];
    return parts.join('-');
  }

  /// Whether [value] is a syntactically valid UUID (any version).
  static bool isValid(String value) {
    final s = value.toLowerCase();
    final re = RegExp(
      r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    );
    if (!re.hasMatch(s)) return false;
    final versionDigit = s[14];
    if (!'12345678'.contains(versionDigit)) return false;
    final variantChar = s[19];
    if (!'89ab'.contains(variantChar)) return false;
    return true;
  }

  /// The version digit (1..8) or null when invalid.
  static int? versionOf(String value) {
    if (!isValid(value)) return null;
    return int.parse(value[14]);
  }

  /// Parses the Unix timestamp (milliseconds) embedded in a v7 UUID.
  static int? timestampMillis(String value) {
    if (versionOf(value) != 7) return null;
    final s = value.replaceAll('-', '').toLowerCase();
    final hex = s.substring(0, 12);
    return int.parse(hex, radix: 16);
  }

  /// Sorts UUID strings lexicographically (case-insensitive).
  static List<String> sort(List<String> values) {
    final copy = List<String>.from(values);
    copy.sort((a, b) => a.toLowerCase().compareTo(b.toLowerCase()));
    return copy;
  }
}
