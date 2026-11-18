// ignore_for_file: file_names
//
// The script is named after the package slug so `dart run bin/<slug>.dart`
// matches the command name in the README; the lints rule wants underscores.

import 'dart:convert';
import 'dart:io';

import 'package:{{ package_name }}/{{ package_name }}.dart';
import 'package:{{ package_name }}/src/options.dart';

const String programName = '{{ npm_name }}';

Future<void> main(List<String> arguments) async {
  exitCode = await run(arguments, stdin, stdout, stderr);
}

/// Turns argv into output and an exit code.
///
/// Exit codes are part of the contract: `0` success, `1` unreadable input, a
/// bad document or a failed `--check`, `2` bad usage.
Future<int> run(
  List<String> arguments,
  Stream<List<int>> input,
  IOSink out,
  IOSink err,
) async {
  final options = Options.parse(arguments);
  switch (options.status) {
    case ParseStatus.help:
      out.write(Options.usage(programName));
      return 0;
    case ParseStatus.error:
      err.writeln('error: ${options.error}');
      err.writeln();
      err.write(Options.usage(programName));
      return 2;
    case ParseStatus.ok:
      break;
  }

  final raw = await _read(options.file, input);
  if (raw == null) {
    err.writeln('error: cannot read ${options.file ?? 'stdin'}');
    return 1;
  }

  final String rendered;
  try {
    rendered = canonicalizeText(raw);
  } on CanonicalError catch (error) {
    err.writeln('error: ${error.message}');
    return 1;
  }

  if (options.check) {
    if (raw.trim() == rendered) {
      out.writeln('canonical');
      return 0;
    }
    err.writeln('not canonical');
    return 1;
  }

  if (options.pretty) {
    out.writeln(pretty(raw));
  } else {
    out.writeln(rendered);
  }
  return 0;
}

Future<String?> _read(String? path, Stream<List<int>> input) async {
  try {
    if (path == null || path == '-') {
      final bytes = await input.expand((chunk) => chunk).toList();
      return utf8.decode(bytes);
    }
    return await File(path).readAsString();
  } on FileSystemException {
    return null;
  } on FormatException {
    return null;
  }
}
