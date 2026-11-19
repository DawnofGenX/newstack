// ignore_for_file: file_names

import 'dart:io';

import 'package:{{ package_name }}/{{ package_name }}.dart';

const String programName = '{{ npm_name }}';

Future<void> main(List<String> arguments) async {
  exitCode = await run(arguments, stdin, stdout, stderr);
}

Future<int> run(
  List<String> arguments,
  Stream<List<int>> input,
  IOSink out,
  IOSink err,
) async {
  if (arguments.isEmpty || arguments.first == '--help' || arguments.first == '-h') {
    out.write(usage(programName));
    return 0;
  }
  if (arguments.first == '--version' || arguments.first == '-V') {
    out.writeln('0.1.0');
    return 0;
  }
  final cmd = arguments.first;
  final rest = arguments.sublist(1);
  switch (cmd) {
    case 'gen':
      return _gen(rest, out, err);
    case 'validate':
      return _validate(rest, out, err);
    case 'parse':
      return _parse(rest, out, err);
    case 'sort':
      return _sort(rest, input, out, err);
    default:
      if (cmd.startsWith('-')) {
        err.writeln("unknown option '$cmd'");
      } else {
        err.writeln("unknown command '$cmd'");
      }
      err.writeln();
      err.write(usage(programName));
      return 2;
  }
}

int _gen(List<String> args, IOSink out, IOSink err) {
  var version = 'v4';
  var count = 1;
  var i = 0;
  while (i < args.length) {
    final a = args[i];
    if (a == '-n' || a == '--count') {
      if (i + 1 >= args.length) {
        err.writeln('error: missing value for $a');
        return 2;
      }
      count = int.tryParse(args[i + 1]) ?? 0;
      if (count < 1) {
        err.writeln('error: count must be positive');
        return 2;
      }
      i += 2;
      continue;
    }
    if (a == 'v4' || a == 'v7' || a == '4' || a == '7') {
      version = a.startsWith('v') ? a : 'v$a';
      i += 1;
      continue;
    }
    err.writeln("unknown option '$a'");
    err.writeln();
    err.write(usage(programName));
    return 2;
  }
  for (var n = 0; n < count; n++) {
    out.writeln(version == 'v7' ? Uuid.v7() : Uuid.v4());
  }
  return 0;
}

int _validate(List<String> args, IOSink out, IOSink err) {
  if (args.isEmpty) {
    err.writeln('error: validate requires at least one UUID');
    return 2;
  }
  var failed = false;
  for (final a in args) {
    final ok = Uuid.isValid(a);
    out.writeln('$a ${ok ? "valid" : "invalid"}');
    if (!ok) failed = true;
  }
  return failed ? 1 : 0;
}

int _parse(List<String> args, IOSink out, IOSink err) {
  if (args.length != 1) {
    err.writeln('error: parse requires exactly one UUID');
    return 2;
  }
  final v = args.first;
  if (!Uuid.isValid(v)) {
    err.writeln("error: invalid UUID '$v'");
    return 1;
  }
  final ver = Uuid.versionOf(v);
  out.writeln('version: $ver');
  final ts = Uuid.timestampMillis(v);
  if (ts != null) {
    out.writeln('timestamp_ms: $ts');
  }
  return 0;
}

Future<int> _sort(List<String> args, Stream<List<int>> input, IOSink out, IOSink err) async {
  final values = <String>[];
  if (args.isEmpty) {
    final bytes = await _readAll(input);
    final text = String.fromCharCodes(bytes);
    for (final line in text.split('\n')) {
      final t = line.trim();
      if (t.isNotEmpty) values.add(t);
    }
  } else {
    for (final path in args) {
      if (path == '-') {
        final bytes = await _readAll(input);
        final text = String.fromCharCodes(bytes);
        for (final line in text.split('\n')) {
          final t = line.trim();
          if (t.isNotEmpty) values.add(t);
        }
      } else {
        try {
          final f = File(path);
          final text = f.readAsStringSync();
          for (final line in text.split('\n')) {
            final t = line.trim();
            if (t.isNotEmpty) values.add(t);
          }
        } on FileSystemException {
          err.writeln("error: cannot open '$path'");
          return 1;
        }
      }
    }
  }
  for (final v in Uuid.sort(values)) {
    out.writeln(v);
  }
  return 0;
}

Future<List<int>> _readAll(Stream<List<int>> input) async {
  final bytes = <int>[];
  await for (final chunk in input) {
    bytes.addAll(chunk);
  }
  return bytes;
}

String usage(String program) =>
    'usage: $program <command> [options]\n'
    '\n'
    'Commands:\n'
    '  gen [v4|v7] [-n COUNT]   generate UUIDs (default v4, count 1)\n'
    '  validate UUID...         validate one or more UUIDs\n'
    '  parse UUID               show version and embedded timestamp\n'
    '  sort [FILE...]           sort UUIDs (stdin if no file)\n'
    '\n'
    '  -h, --help               show this help and exit\n'
    '  -V, --version            show version and exit\n';
