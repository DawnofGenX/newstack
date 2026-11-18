/// Thrown when CSV input cannot be parsed.
class CsvException implements Exception {
  CsvException(this.message);

  /// A human readable reason, already prefixed with the row when known.
  final String message;

  @override
  String toString() => message;
}

/// A parsed CSV table: one header row plus data rows of the same width.
final class CsvTable {
  CsvTable(List<String> headers, List<List<String>> rows)
    : headers = List<String>.unmodifiable(headers),
      rows = List<List<String>>.unmodifiable(
        rows.map((row) => List<String>.unmodifiable(row)),
      );

  /// Parses RFC 4180 text: doubled quotes, quoted delimiters and newlines.
  ///
  /// Throws [CsvException] for an unterminated quote, an empty document or a
  /// row whose width does not match the header.
  factory CsvTable.parse(String text, {String delimiter = ','}) {
    if (delimiter.length != 1) {
      throw CsvException('delimiter must be a single character');
    }
    final parsed = <List<String>>[];
    var row = <String>[];
    final field = StringBuffer();
    var quoted = false;
    var index = 0;

    while (index < text.length) {
      final char = text[index];
      if (quoted) {
        if (char == '"') {
          final doubled = index + 1 < text.length && text[index + 1] == '"';
          if (doubled) {
            field.write('"');
            index += 2;
            continue;
          }
          quoted = false;
          index++;
          continue;
        }
        field.write(char);
        index++;
        continue;
      }
      if (char == '"' && field.isEmpty) {
        quoted = true;
        index++;
        continue;
      }
      if (char == delimiter) {
        row.add(field.toString());
        field.clear();
        index++;
        continue;
      }
      if (char == '\r') {
        index++;
        continue;
      }
      if (char == '\n') {
        row.add(field.toString());
        field.clear();
        parsed.add(row);
        row = <String>[];
        index++;
        continue;
      }
      field.write(char);
      index++;
    }

    if (quoted) {
      throw CsvException('unterminated quoted field');
    }
    if (field.isNotEmpty || row.isNotEmpty) {
      row.add(field.toString());
      parsed.add(row);
    }
    if (parsed.isEmpty) {
      throw CsvException('the document has no rows');
    }

    final headers = parsed.first;
    final rows = parsed.skip(1).toList();
    for (var index = 0; index < rows.length; index++) {
      if (rows[index].length != headers.length) {
        throw CsvException(
          'row ${index + 2} has ${rows[index].length} fields, expected ${headers.length}',
        );
      }
    }
    return CsvTable(headers, rows);
  }

  /// The header cells, in document order.
  final List<String> headers;

  /// The data rows; every row has `headers.length` cells.
  final List<List<String>> rows;

  /// The number of data rows.
  int get length => rows.length;

  /// The zero based index of [name], which may also be a 1 based position.
  int indexOf(String name) {
    final byName = headers.indexOf(name);
    if (byName >= 0) {
      return byName;
    }
    final position = int.tryParse(name);
    if (position != null && position >= 1 && position <= headers.length) {
      return position - 1;
    }
    throw CsvException("unknown column '$name'");
  }

  /// A copy containing only [names], in the order given.
  CsvTable select(List<String> names) {
    final indexes = names.map(indexOf).toList();
    return CsvTable(
      indexes.map((index) => headers[index]).toList(),
      rows.map((row) => indexes.map((index) => row[index]).toList()).toList(),
    );
  }

  /// The rows as maps keyed by header, in document order.
  List<Map<String, String>> asMaps() {
    return rows
        .map(
          (row) => <String, String>{
            for (var index = 0; index < headers.length; index++)
              headers[index]: row[index],
          },
        )
        .toList();
  }

  /// Renders the table, quoting only the fields that need it.
  String render({String delimiter = ','}) {
    final buffer = StringBuffer();
    void writeRow(List<String> row) {
      buffer.writeln(row.map((cell) => _quote(cell, delimiter)).join(delimiter));
    }

    writeRow(headers);
    rows.forEach(writeRow);
    return buffer.toString();
  }

  static String _quote(String cell, String delimiter) {
    final needsQuotes = cell.contains(delimiter) ||
        cell.contains('"') ||
        cell.contains('\n') ||
        cell.contains('\r') ||
        (cell.isNotEmpty && (cell.startsWith(' ') || cell.endsWith(' ')));
    if (!needsQuotes) {
      return cell;
    }
    return '"${cell.replaceAll('"', '""')}"';
  }
}
