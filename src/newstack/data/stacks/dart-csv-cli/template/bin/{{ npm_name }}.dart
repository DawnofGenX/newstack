// ignore_for_file: file_names
//
// The script is named after the package slug so `dart run bin/<slug>.dart`
// matches the command name in the README; the lints rule wants underscores.

import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:{{ package_name }}/{{ package_name }}.dart';

const String programName = '{{ npm_name }}';

Future<void> main(List<String> arguments) async {
  exitCode = await run(arguments, stdin, stdout, stderr);
}

/// Turns argv into output and an exit code.
///
/// Exit codes are part of the contract: `0` success, `1` unreadable input or a
/// bad document, `2` bad usage.
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

  final text = await _read(options.files, input, err);
  if (text == null) {
    return 1;
  }

  try {
    var table = CsvTable.parse(text, delimiter: options.delimiter);
    if (options.columns.isNotEmpty) {
      table = table.select(options.columns);
    }
    if (options.asJson) {
      out.writeln(jsonEncode(table.asMaps()));
    } else {
      out.write(table.render(delimiter: options.delimiter));
    }
    return 0;
  } on CsvException catch (error) {
    err.writeln('error: ${error.message}');
    return 1;
  }
}

/// Reads every file, or standard input when none is named; null means failure.
Future<String?> _read(
  List<String> files,
  Stream<List<int>> input,
  IOSink err,
) async {
  if (files.isEmpty) {
    return _drain(input);
  }
  final parts = <String>[];
  for (final path in files) {
    if (path == '-') {
      parts.add(await _drain(input));
      continue;
    }
    try {
      parts.add(File(path).readAsStringSync());
    } on FileSystemException {
      err.writeln("error: cannot open '$path'");
      return null;
    }
  }
  return parts.join('\n');
}

/// Drains a byte stream so standard input can be re-read as text.
Future<String> _drain(Stream<List<int>> input) async {
  final builder = BytesBuilder(copy: false);
  await for (final chunk in input) {
    builder.add(chunk);
  }
  return utf8.decode(builder.takeBytes());
}
