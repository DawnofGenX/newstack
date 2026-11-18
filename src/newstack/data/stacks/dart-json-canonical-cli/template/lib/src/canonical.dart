import 'dart:convert';

/// Raised when a value cannot be represented as canonical JSON.
class CanonicalError implements Exception {
  CanonicalError(this.message);

  final String message;

  @override
  String toString() => message;
}

/// Renders [value] the way RFC 8785 orders and formats it.
///
/// Object keys sort by UTF-16 code unit, numbers lose a trailing `.0` and any
/// `-0`, and the output carries no whitespace at all. Anything JSON cannot
/// express (NaN, infinity, non-string map keys) is refused instead of being
/// silently rewritten.
String canonicalize(Object? value) {
  final buffer = StringBuffer();
  _write(value, buffer);
  return buffer.toString();
}

/// Parses [text] and returns its canonical rendering.
String canonicalizeText(String text) {
  Object? decoded;
  try {
    decoded = jsonDecode(text);
  } on FormatException catch (error) {
    throw CanonicalError('invalid JSON: ${error.message}');
  }
  return canonicalize(decoded);
}

/// Re-indents a canonical document for reading, keeping the sorted key order.
String pretty(String text, {String indent = '  '}) {
  return const JsonEncoder.withIndent('  ').convert(jsonDecode(canonicalizeText(text)));
}

void _write(Object? value, StringBuffer buffer) {
  if (value == null) {
    buffer.write('null');
  } else if (value is bool) {
    buffer.write(value ? 'true' : 'false');
  } else if (value is num) {
    buffer.write(formatNumber(value));
  } else if (value is String) {
    _writeString(value, buffer);
  } else if (value is List) {
    buffer.write('[');
    for (var index = 0; index < value.length; index++) {
      if (index > 0) buffer.write(',');
      _write(value[index], buffer);
    }
    buffer.write(']');
  } else if (value is Map) {
    final keys = value.keys.map((key) {
      if (key is String) return key;
      throw CanonicalError('object keys must be strings, got ${key.runtimeType}');
    }).toList()
      ..sort(_compareKeys);
    buffer.write('{');
    for (var index = 0; index < keys.length; index++) {
      if (index > 0) buffer.write(',');
      _writeString(keys[index], buffer);
      buffer.write(':');
      _write(value[keys[index]], buffer);
    }
    buffer.write('}');
  } else {
    throw CanonicalError('cannot canonicalise ${value.runtimeType}');
  }
}

/// Sorts by UTF-16 code unit, which is what RFC 8785 asks for.
int _compareKeys(String left, String right) {
  final a = left.codeUnits;
  final b = right.codeUnits;
  final shared = a.length < b.length ? a.length : b.length;
  for (var index = 0; index < shared; index++) {
    if (a[index] != b[index]) return a[index] - b[index];
  }
  return a.length - b.length;
}

/// Formats a number the way ECMAScript's Number#toString does for the values a
/// JSON document can hold: whole numbers lose the fraction, `-0` becomes `0`.
String formatNumber(num value) {
  if (value is int) return value.toString();
  final double number = value.toDouble();
  if (number.isNaN || number.isInfinite) {
    throw CanonicalError('$number is not representable in JSON');
  }
  if (number == 0) return '0';
  if (number == number.roundToDouble() && number.abs() < 1e21) {
    return number.toStringAsFixed(0);
  }
  return number.toString();
}

void _writeString(String value, StringBuffer buffer) {
  buffer.write('"');
  for (final rune in value.runes) {
    switch (rune) {
      case 0x22:
        buffer.write(r'\"');
      case 0x5c:
        buffer.write(r'\\');
      case 0x08:
        buffer.write(r'\b');
      case 0x09:
        buffer.write(r'\t');
      case 0x0a:
        buffer.write(r'\n');
      case 0x0c:
        buffer.write(r'\f');
      case 0x0d:
        buffer.write(r'\r');
      default:
        if (rune < 0x20) {
          buffer.write('\\u${rune.toRadixString(16).padLeft(4, '0')}');
        } else {
          buffer.writeCharCode(rune);
        }
    }
  }
  buffer.write('"');
}
