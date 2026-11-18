import 'package:{{ package_name }}/{{ package_name }}.dart';
import 'package:test/test.dart';

void main() {
  test('parses plain rows', () {
    final table = CsvTable.parse('name,city\nanna,delhi\nbo,poona\n');
    expect(table.headers, ['name', 'city']);
    expect(table.length, 2);
    expect(table.rows[1], ['bo', 'poona']);
  });

  test('parses quoted delimiters, doubled quotes and newlines', () {
    final table = CsvTable.parse('a,b\n"x,y","he said ""hi""\nnext"\n');
    expect(table.rows.single[0], 'x,y');
    expect(table.rows.single[1], 'he said "hi"\nnext');
  });

  test('tolerates CRLF and a missing final newline', () {
    final table = CsvTable.parse('a,b\r\n1,2');
    expect(table.rows.single, ['1', '2']);
  });

  test('rejects a ragged row with the row number', () {
    expect(
      () => CsvTable.parse('a,b\n1,2,3\n'),
      throwsA(
        isA<CsvException>().having(
          (error) => error.message,
          'message',
          'row 2 has 3 fields, expected 2',
        ),
      ),
    );
  });

  test('rejects an unterminated quote', () {
    expect(() => CsvTable.parse('a\n"open\n'), throwsA(isA<CsvException>()));
  });

  test('selects by name and by 1 based position', () {
    final table = CsvTable.parse('a,b,c\n1,2,3\n');
    expect(table.select(['c', '1']).headers, ['c', 'a']);
    expect(table.select(['3']).rows.single, ['3']);
  });

  test('an unknown column names itself', () {
    final table = CsvTable.parse('a\n1\n');
    expect(
      () => table.select(['zz']),
      throwsA(
        isA<CsvException>().having(
          (error) => error.message,
          'message',
          "unknown column 'zz'",
        ),
      ),
    );
  });

  test('renders with quotes only where needed', () {
    final table = CsvTable(['a', 'b'], [['x,y', 'plain']]);
    expect(table.render(), 'a,b\n"x,y",plain\n');
  });

  test('honours a custom delimiter', () {
    final table = CsvTable.parse('a;b\n1;2\n', delimiter: ';');
    expect(table.rows.single, ['1', '2']);
    expect(table.render(delimiter: ';'), 'a;b\n1;2\n');
  });

  test('asMaps keys by header', () {
    final table = CsvTable.parse('a,b\n1,2\n');
    expect(table.asMaps(), [
      {'a': '1', 'b': '2'},
    ]);
  });
}
