import 'package:{{ package_name }}/{{ package_name }}.dart';
import 'package:test/test.dart';

void main() {
  group('Options.parse', () {
    test('defaults to every figure and no files', () {
      final options = Options.parse(const <String>[]);
      expect(options.status, ParseStatus.ok);
      expect(options.mode, Mode.all);
      expect(options.files, isEmpty);
    });

    test('selects one mode per short or long flag', () {
      expect(Options.parse(const <String>['-l']).mode, Mode.lines);
      expect(Options.parse(const <String>['--words']).mode, Mode.words);
      expect(Options.parse(const <String>['-c', 'a.txt']).mode, Mode.bytes);
    });

    test('rejects conflicting modes', () {
      final options = Options.parse(const <String>['-l', '-w']);
      expect(options.status, ParseStatus.error);
      expect(options.error, contains('conflicts'));
    });

    test('rejects an unknown option', () {
      final options = Options.parse(const <String>['--nope']);
      expect(options.status, ParseStatus.error);
      expect(options.error, "unknown option '--nope'");
    });

    test('treats everything after -- as a file name', () {
      final options = Options.parse(const <String>['--', '-w']);
      expect(options.status, ParseStatus.ok);
      expect(options.mode, Mode.all);
      expect(options.files, const <String>['-w']);
    });

    test('keeps - as a file, meaning standard input', () {
      expect(Options.parse(const <String>['-']).files, const <String>['-']);
    });

    test('stops parsing at --help and --version', () {
      expect(Options.parse(const <String>['a.txt', '--help']).status,
          ParseStatus.help);
      expect(Options.parse(const <String>['-V']).status, ParseStatus.version);
    });
  });

  test('usage names the program it was generated for', () {
    expect(Options.usage('textstat'), startsWith('usage: textstat'));
    expect(Options.usage('textstat'), contains('--bytes'));
  });
}
