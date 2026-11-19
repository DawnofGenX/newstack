import 'dart:io';

import 'package:test/test.dart';

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
    });

    test('validate bad uuid exits 1', () async {
      final result = await runCli(const <String>['validate', 'not-a-uuid']);
      expect(result.exitCode, 1);
    });

    test('gen v4 outputs valid uuid', () async {
      final result = await runCli(const <String>['gen', 'v4']);
      expect(result.exitCode, 0);
      expect(result.stdout.trim().split('\n').length, 1);
    });

    test('gen -n 3 outputs 3', () async {
      final result = await runCli(const <String>['gen', 'v4', '-n', '3']);
      expect(result.exitCode, 0);
      expect(result.stdout.trim().split('\n').length, 3);
    });

    test('parse v7 prints timestamp', () async {
      final gen = await runCli(const <String>['gen', 'v7']);
      final u = gen.stdout.trim();
      final result = await runCli(<String>['parse', u]);
      expect(result.exitCode, 0);
      expect(result.stdout, contains('timestamp_ms:'));
    });

    test('validate valid uuid exits 0', () async {
      final result = await runCli(const <String>['validate', '550e8400-e29b-41d4-a716-446655440000']);
      expect(result.exitCode, 0);
    });
  });
}
