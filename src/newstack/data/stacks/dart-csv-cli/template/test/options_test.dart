import 'package:{{ package_name }}/{{ package_name }}.dart';
import 'package:test/test.dart';

void main() {
  test('defaults to comma and standard input', () {
    final options = Options.parse(const []);
    expect(options.delimiter, ',');
    expect(options.files, isEmpty);
    expect(options.status, ParseStatus.ok);
  });

  test('reads the delimiter, including the word tab', () {
    expect(Options.parse(const ['-d', ';']).delimiter, ';');
    expect(Options.parse(const ['--delimiter', 'tab']).delimiter, '\t');
  });

  test('lists columns and files in order', () {
    final options = Options.parse(const ['-c', 'a,b', 'one.csv', '-']);
    expect(options.columns, ['a', 'b']);
    expect(options.files, ['one.csv', '-']);
  });

  test('treats everything after -- as a file', () {
    expect(Options.parse(const ['--', '--json']).files, ['--json']);
  });

  test('errors name the offending option', () {
    expect(Options.parse(const ['--bogus']).error, "unknown option '--bogus'");
    expect(
      Options.parse(const ['-d', 'long']).error,
      "delimiter must be one character, got 'long'",
    );
    expect(Options.parse(const ['-c']).status, ParseStatus.error);
  });

  test('help wins', () {
    expect(Options.parse(const ['--help']).status, ParseStatus.help);
  });
}
