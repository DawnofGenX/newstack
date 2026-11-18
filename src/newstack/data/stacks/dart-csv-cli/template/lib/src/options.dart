/// How parsing ended, which decides the exit code in the entry point.
enum ParseStatus { ok, help, error }

/// A parsed command line: delimiter, selected columns, output mode and files.
final class Options {
  Options({
    required this.delimiter,
    required List<String> columns,
    required List<String> files,
    required this.asJson,
    required this.status,
    this.error = '',
  }) : columns = List<String>.unmodifiable(columns),
       files = List<String>.unmodifiable(files);

  /// The field separator, one character.
  final String delimiter;

  /// Column names or 1 based positions to keep, in output order.
  final List<String> columns;

  /// Files to read, in order; `-` means standard input.
  final List<String> files;

  /// Whether to print a JSON array of objects instead of CSV.
  final bool asJson;

  /// How parsing ended.
  final ParseStatus status;

  /// The message for [ParseStatus.error], and empty otherwise.
  final String error;

  /// Hand-rolled parser: no dependency, and every branch is unit tested.
  static Options parse(List<String> args) {
    var delimiter = ',';
    final columns = <String>[];
    final files = <String>[];
    var asJson = false;
    var onlyFiles = false;

    for (var index = 0; index < args.length; index++) {
      final argument = args[index];
      if (onlyFiles || argument == '-' || argument.isEmpty) {
        files.add(argument);
        continue;
      }
      if (argument == '--') {
        onlyFiles = true;
        continue;
      }
      if (argument == '-h' || argument == '--help') {
        return Options(
          delimiter: delimiter,
          columns: columns,
          files: files,
          asJson: asJson,
          status: ParseStatus.help,
        );
      }
      if (argument == '--json') {
        asJson = true;
        continue;
      }
      if (argument == '-d' || argument == '--delimiter') {
        final value = _next(args, index);
        if (value == null) {
          return _failure('option $argument needs a value');
        }
        final resolved = value == 'tab' ? '\t' : value;
        if (resolved.length != 1) {
          return _failure("delimiter must be one character, got '$value'");
        }
        delimiter = resolved;
        index++;
        continue;
      }
      if (argument == '-c' || argument == '--columns') {
        final value = _next(args, index);
        if (value == null) {
          return _failure('option $argument needs a value');
        }
        for (final name in value.split(',')) {
          final trimmed = name.trim();
          if (trimmed.isEmpty) {
            return _failure('column list contains an empty name');
          }
          columns.add(trimmed);
        }
        index++;
        continue;
      }
      if (argument.startsWith('-')) {
        return _failure("unknown option '$argument'");
      }
      files.add(argument);
    }

    return Options(
      delimiter: delimiter,
      columns: columns,
      files: files,
      asJson: asJson,
      status: ParseStatus.ok,
    );
  }

  static String? _next(List<String> args, int index) =>
      index + 1 < args.length ? args[index + 1] : null;

  static Options _failure(String message) => Options(
    delimiter: ',',
    columns: const <String>[],
    files: const <String>[],
    asJson: false,
    status: ParseStatus.error,
    error: message,
  );

  /// The help text; the program name comes from the caller.
  static String usage(String program) =>
      'usage: $program [-d DELIMITER] [-c COLUMNS] [--json] [--] [FILE ...]\n'
      '\n'
      'Reads CSV from the files or standard input and prints the selected columns.\n'
      '\n'
      '  -d, --delimiter CHAR   field separator, or the word tab (default ,)\n'
      '  -c, --columns LIST     comma separated names or 1 based positions\n'
      '      --json             print a JSON array of objects\n'
      '  -h, --help             print this message\n';
}
