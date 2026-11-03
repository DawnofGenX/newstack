import 'dart:io';

import 'package:test/test.dart';

/// The exit codes are part of the contract, so they are tested through the real
/// script rather than by calling internals.
const String script = 'bin/{{ npm_name }}.dart';

Future<ProcessResult> runCli(List<String> arguments) =>
    Process.run(Platform.resolvedExecutable, <String>[script, ...arguments]);

void main() {
  group('exit codes', () {
    test('--help prints usage and exits 0', () async {
      final result = await runCli(const <String>['--help']);
      expect(result.exitCode, 0);
      expect(result.stdout, contains('usage: {{ npm_name }}'));
    });

    test('an unknown flag exits 2', () async {
      final result = await runCli(const <String>['--bogus']);
      expect(result.exitCode, 2);
      expect(result.stderr, contains("unknown option '--bogus'"));
    });

    test('an unreadable file exits 1', () async {
      final result = await runCli(const <String>['no-such-file.txt']);
      expect(result.exitCode, 1);
      expect(result.stderr, contains("cannot open 'no-such-file.txt'"));
    });
  });

  test('prints a line, word and byte count for a file', () async {
    final directory = await Directory.systemTemp.createTemp('newstack');
    addTearDown(() => directory.delete(recursive: true));
    final file = File('${directory.path}/sample.txt')
      ..writeAsStringSync('one two\nthree\n');

    final result = await runCli(<String>[file.path]);

    expect(result.exitCode, 0);
    final fields = result.stdout.trim().split(RegExp(r'\s+'));
    expect(fields.take(3), <String>['2', '3', '14']);
    expect(result.stdout, endsWith('${file.path}\n'));
  });
}
