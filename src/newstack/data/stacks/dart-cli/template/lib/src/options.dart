/// Which figures to print; [Mode.all] prints lines, words and bytes.
enum Mode { all, lines, words, bytes }

/// How parsing ended, which decides the exit code in the entry point.
enum ParseStatus { ok, help, version, error }

/// A parsed command line: the chosen mode, the files and the outcome.
final class Options {
  Options({
    required this.mode,
    required List<String> files,
    required this.status,
    this.error = '',
  }) : files = List<String>.unmodifiable(files);

  /// The version reported by `--version`.
  static const String version = '0.1.0';

  /// Which figures to print.
  final Mode mode;

  /// Files to read, in order; `-` means standard input.
  final List<String> files;

  /// How parsing ended.
  final ParseStatus status;

  /// The message for [ParseStatus.error], and empty otherwise.
  final String error;

  /// Hand-rolled parser: no dependency, and every branch is unit tested.
  static Options parse(List<String> args) {
    Mode? chosen;
    var onlyFiles = false;
    final files = <String>[];

    for (final arg in args) {
      if (onlyFiles || arg.isEmpty || arg == '-') {
        files.add(arg);
        continue;
      }
      if (arg == '--') {
        onlyFiles = true;
        continue;
      }
      if (arg == '-h' || arg == '--help') {
        return Options(
          mode: chosen ?? Mode.all,
          files: files,
          status: ParseStatus.help,
        );
      }
      if (arg == '-V' || arg == '--version') {
        return Options(
          mode: chosen ?? Mode.all,
          files: files,
          status: ParseStatus.version,
        );
      }
      final requested = _modeFor(arg);
      if (requested != null) {
        if (chosen != null && chosen != requested) {
          return Options(
            mode: chosen,
            files: files,
            status: ParseStatus.error,
            error: "choose one of -l, -w, -c: '$arg' conflicts with an earlier mode",
          );
        }
        chosen = requested;
        continue;
      }
      if (arg.startsWith('-')) {
        return Options(
          mode: chosen ?? Mode.all,
          files: files,
          status: ParseStatus.error,
          error: "unknown option '$arg'",
        );
      }
      files.add(arg);
    }

    return Options(
      mode: chosen ?? Mode.all,
      files: files,
      status: ParseStatus.ok,
    );
  }

  /// The help text; the program name comes from the caller so it matches the
  /// script that is actually being run.
  static String usage(String program) =>
      'usage: $program [-l | -w | -c] [--] [FILE ...]\n'
      '\n'
      'Count lines, words and bytes in each FILE, or in standard input\n'
      'when no FILE is given. With more than one FILE a total is printed.\n'
      '\n'
      '  -l, --lines     print the line count only\n'
      '  -w, --words     print the word count only\n'
      '  -c, --bytes     print the byte count only\n'
      '  -h, --help      show this help and exit\n'
      '  -V, --version   show the version and exit\n';

  static Mode? _modeFor(String arg) => switch (arg) {
        '-l' || '--lines' => Mode.lines,
        '-w' || '--words' => Mode.words,
        '-c' || '--bytes' => Mode.bytes,
        _ => null,
      };
}
