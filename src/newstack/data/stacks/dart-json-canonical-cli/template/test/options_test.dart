import 'package:test/test.dart';
import 'package:{{ package_name }}/src/options.dart';

void main() {
  test('defaults to stdin and canonical output', () {
    final options = Options.parse([]);
    expect(options.status, ParseStatus.ok);
    expect(options.file, isNull);
    expect(options.pretty, isFalse);
    expect(options.check, isFalse);
  });

  test('takes a file plus flags in any order', () {
    final options = Options.parse(['-p', 'data.json']);
    expect(options.status, ParseStatus.ok);
    expect(options.file, 'data.json');
    expect(options.pretty, isTrue);
  });

  test('accepts long flags', () {
    expect(Options.parse(['--check', 'a.json']).check, isTrue);
    expect(Options.parse(['--pretty']).pretty, isTrue);
  });

  test('treats -- as the end of options', () {
    final options = Options.parse(['--', '--weird-name.json']);
    expect(options.status, ParseStatus.ok);
    expect(options.file, '--weird-name.json');
  });

  test('reports unknown options', () {
    final options = Options.parse(['--bogus']);
    expect(options.status, ParseStatus.error);
    expect(options.error, contains('unknown option'));
  });

  test('rejects two files', () {
    final options = Options.parse(['a.json', 'b.json']);
    expect(options.status, ParseStatus.error);
    expect(options.error, contains('at most one file'));
  });

  test('refuses --pretty with --check', () {
    final options = Options.parse(['--pretty', '--check']);
    expect(options.status, ParseStatus.error);
    expect(options.error, contains('mutually exclusive'));
  });

  test('usage names the program', () {
    expect(Options.usage('jsonc'), contains('Usage: jsonc'));
  });
}
