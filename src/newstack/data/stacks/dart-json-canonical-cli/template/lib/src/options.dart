/// Command line parsing kept separate from the CLI so it can be unit tested.
library;

enum ParseStatus { ok, help, error }

class Options {
  Options({
    required this.file,
    required this.pretty,
    required this.check,
    this.status = ParseStatus.ok,
    this.error = '',
  });

  final String? file;
  final bool pretty;
  final bool check;
  final ParseStatus status;
  final String error;

  static const String _usage = 'Usage: PROGRAM [options] [FILE]\n'
      '\n'
      'Renders JSON in canonical form: object keys sorted by UTF-16 code unit, no\n'
      'whitespace, numbers without a redundant fraction. Reads stdin when no FILE\n'
      'is given ("-" also means stdin).\n'
      '\n'
      'Options:\n'
      '  -p, --pretty    re-indent the canonical document for reading\n'
      '  -c, --check     exit 1 when the input is not already canonical\n'
      '  -h, --help      show this help\n';

  static String usage(String program) => _usage.replaceAll('PROGRAM', program);

  factory Options.parse(List<String> arguments) {
    String? file;
    var pretty = false;
    var check = false;
    var sawDashDash = false;

    Options fail(String message) => Options(
          file: null,
          pretty: false,
          check: false,
          status: ParseStatus.error,
          error: message,
        );

    for (var index = 0; index < arguments.length; index++) {
      final argument = arguments[index];
      if (!sawDashDash && argument == '--') {
        sawDashDash = true;
        continue;
      }
      if (!sawDashDash && (argument == '-h' || argument == '--help')) {
        return Options(file: null, pretty: false, check: false, status: ParseStatus.help);
      }
      if (!sawDashDash && (argument == '-p' || argument == '--pretty')) {
        pretty = true;
        continue;
      }
      if (!sawDashDash && (argument == '-c' || argument == '--check')) {
        check = true;
        continue;
      }
      if (!sawDashDash && argument.startsWith('-') && argument != '-') {
        return fail('unknown option "$argument"');
      }
      if (file != null) {
        return fail('expected at most one file, got "$file" and "$argument"');
      }
      file = argument;
    }

    if (pretty && check) {
      return fail('--pretty and --check are mutually exclusive');
    }
    return Options(file: file, pretty: pretty, check: check);
  }
}
