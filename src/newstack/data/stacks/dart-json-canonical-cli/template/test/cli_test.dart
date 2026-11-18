import 'dart:convert';
import 'dart:io';

import 'package:test/test.dart';

/// Runs the real script so the exit codes are covered end to end.
Future<ProcessResult> _cli(List<String> arguments, {String? stdinText}) async {
  final process = await Process.start(
    Platform.resolvedExecutable,
    ['run', 'bin/{{ npm_name }}.dart', ...arguments],
  );
  if (stdinText != null) {
    process.stdin.write(stdinText);
  }
  await process.stdin.close();
  final out = await process.stdout.transform(utf8.decoder).join();
  final err = await process.stderr.transform(utf8.decoder).join();
  final code = await process.exitCode;
  return ProcessResult(process.pid, code, out, err);
}

void main() {
  test('canonicalises stdin', () async {
    final result = await _cli([], stdinText: '{"b": 2, "a": 1}');
    expect(result.exitCode, 0);
    expect((result.stdout as String).trim(), '{"a":1,"b":2}');
  });

  test('prints a pretty document with -p', () async {
    final result = await _cli(['-p'], stdinText: '{"b":2,"a":1}');
    expect(result.exitCode, 0);
    expect(result.stdout, '{\n  "a": 1,\n  "b": 2\n}\n');
  });

  test('--check accepts canonical input', () async {
    final result = await _cli(['--check'], stdinText: '{"a":1,"b":2}');
    expect(result.exitCode, 0);
    expect((result.stdout as String).trim(), 'canonical');
  });

  test('--check rejects reordered input', () async {
    final result = await _cli(['--check'], stdinText: '{"b":2,"a":1}');
    expect(result.exitCode, 1);
    expect((result.stderr as String).trim(), 'not canonical');
  });

  test('malformed JSON exits 1', () async {
    final result = await _cli([], stdinText: '{"a": }');
    expect(result.exitCode, 1);
    expect(result.stderr, contains('invalid JSON'));
  });

  test('a missing file exits 1', () async {
    final result = await _cli(['no-such-file.json']);
    expect(result.exitCode, 1);
    expect(result.stderr, contains('cannot read'));
  });

  test('--help exits 0', () async {
    final result = await _cli(['--help']);
    expect(result.exitCode, 0);
    expect(result.stdout, contains('Usage: {{ npm_name }}'));
  });

  test('an unknown option exits 2', () async {
    final result = await _cli(['--bogus']);
    expect(result.exitCode, 2);
    expect(result.stderr, contains('unknown option'));
  });
}
