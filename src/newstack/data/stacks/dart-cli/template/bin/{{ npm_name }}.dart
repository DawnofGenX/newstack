// ignore_for_file: file_names
//
// The script is named after the package slug so that `dart run bin/<slug>.dart`
// matches the command name in the README; the lints rule wants underscores.

import 'dart:io';

import 'package:{{ package_name }}/{{ package_name }}.dart';

const String programName = '{{ npm_name }}';

Future<void> main(List<String> arguments) async {
  exitCode = await run(arguments, stdin, stdout, stderr);
}

/// Turns argv into output and an exit code.
///
/// Exit codes are part of the contract: `0` success, `1` unreadable input,
/// `2` bad usage. Nothing here calls `exit()`, so the codes stay testable.
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
    case ParseStatus.version:
      out.writeln(Options.version);
      return 0;
    case ParseStatus.error:
      err.writeln('error: ${options.error}');
      err.writeln();
      err.write(Options.usage(programName));
      return 2;
    case ParseStatus.ok:
      break;
  }

  final files = options.files;
  if (files.isEmpty) {
    printCounts(out, TextStat.count(await readAll(input)), options.mode, '');
    return 0;
  }

  var total = Counts.zero;
  var failed = false;
  for (final path in files) {
    Counts counts;
    if (path == '-') {
      counts = TextStat.count(await readAll(input));
      printCounts(out, counts, options.mode, '');
    } else {
      try {
        counts = TextStat.count(File(path).readAsBytesSync());
      } on FileSystemException {
        err.writeln("error: cannot open '$path'");
        failed = true;
        continue;
      }
      printCounts(out, counts, options.mode, path);
    }
    total = total + counts;
  }

  if (files.length > 1) {
    printCounts(out, total, options.mode, 'total');
  }
  return failed ? 1 : 0;
}

/// Prints the requested figures, right-aligned like `wc`, plus a label.
void printCounts(IOSink out, Counts counts, Mode mode, String label) {
  final line = StringBuffer();
  if (mode == Mode.all || mode == Mode.lines) {
    line.write(counts.lines.toString().padLeft(8));
  }
  if (mode == Mode.all || mode == Mode.words) {
    line.write(counts.words.toString().padLeft(8));
  }
  if (mode == Mode.all || mode == Mode.bytes) {
    line.write(counts.bytes.toString().padLeft(8));
  }
  if (label.isNotEmpty) {
    line.write(' $label');
  }
  out.writeln(line);
}

/// Drains a byte stream, so standard input can be counted like a file.
Future<List<int>> readAll(Stream<List<int>> input) async {
  final bytes = <int>[];
  await for (final chunk in input) {
    bytes.addAll(chunk);
  }
  return bytes;
}
