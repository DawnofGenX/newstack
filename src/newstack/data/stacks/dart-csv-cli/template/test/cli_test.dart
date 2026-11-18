import 'dart:io';

import 'package:test/test.dart';

/// The exit codes are part of the contract, so the script is run for real.
const String script = 'bin/{{ npm_name }}.dart';

Future<ProcessResult> runCli(List<String> arguments) =>
    Process.run(Platform.resolvedExecutable, <String>[script, ...arguments]);

void main() {
  late Directory directory;
  late String csvPath;

  setUp(() {
    directory = Directory.systemTemp.createTempSync('newstack-csv');
    csvPath = '${directory.path}/sample.csv';
    File(csvPath).writeAsStringSync('name,city\nanna,delhi\nbo,poona\n');
  });

  tearDown(() => directory.deleteSync(recursive: true));

  test('--help prints usage and exits 0', () async {
    final result = await runCli(const ['--help']);
    expect(result.exitCode, 0);
    expect(result.stdout, contains('usage: {{ npm_name }}'));
  });

  test('an unknown flag exits 2', () async {
    final result = await runCli(const ['--bogus']);
    expect(result.exitCode, 2);
    expect(result.stderr, contains("unknown option '--bogus'"));
  });

  test('an unreadable file exits 1', () async {
    final result = await runCli(const ['no-such-file.csv']);
    expect(result.exitCode, 1);
    expect(result.stderr, contains("cannot open 'no-such-file.csv'"));
  });

  test('prints the whole table', () async {
    final result = await runCli([csvPath]);
    expect(result.exitCode, 0);
    expect(result.stdout, 'name,city\nanna,delhi\nbo,poona\n');
  });

  test('projects one column', () async {
    final result = await runCli(['-c', 'city', csvPath]);
    expect(result.exitCode, 0);
    expect(result.stdout, 'city\ndelhi\npoona\n');
  });

  test('prints JSON objects', () async {
    final result = await runCli(['--json', '-c', 'name', csvPath]);
    expect(result.exitCode, 0);
    expect(result.stdout.trim(), '[{"name":"anna"},{"name":"bo"}]');
  });

  test('a ragged document exits 1', () async {
    final bad = '${directory.path}/bad.csv';
    File(bad).writeAsStringSync('a,b\n1,2,3\n');
    final result = await runCli([bad]);
    expect(result.exitCode, 1);
    expect(result.stderr, contains('row 2 has 3 fields, expected 2'));
  });
}
