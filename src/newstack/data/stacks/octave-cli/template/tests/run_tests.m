1;  % this is a script, not a function file

function check(name, ok)
  global PASSED FAILED;
  if ok
    PASSED = PASSED + 1;
  else
    FAILED = FAILED + 1;
    printf('FAIL %s\n', name);
  end
end

function check_equal(name, actual, expected)
  ok = isequal(actual, expected);
  check(name, ok);
  if ~ok
    printf('  got      %s\n', describe(actual));
    printf('  expected %s\n', describe(expected));
  end
end

function text = describe(value)
  if ischar(value)
    text = [ value ];
  elseif isstruct(value)
    text = '<struct>';
  else
    text = sprintf('%d ', value(:)');
    text = text(1:end - 1);
  end
end

function reset_buffers()
  global OUT_BUF ERR_BUF;
  OUT_BUF = '';
  ERR_BUF = '';
end

function write_out(text)
  global OUT_BUF;
  OUT_BUF = [OUT_BUF text];
end

function write_err(text)
  global ERR_BUF;
  ERR_BUF = [ERR_BUF text];
end

function io = harness_io(sources, stdin_text)
  global READ_PATHS ERR_BUF OUT_BUF;
  READ_PATHS = {};
  io.read_file = @(path) read_source(path, sources);
  io.read_stdin = @() uint8(stdin_text);
  io.write_out = @write_out;
  io.write_err = @write_err;
end

function [data, ok] = read_source(path, sources)
  global READ_PATHS;
  READ_PATHS{end + 1} = path;
  if isfield(sources, path)
    data = uint8(sources.(path));
    ok = true;
  else
    data = uint8([]);
    ok = false;
  end
end

function path = only_path()
  global READ_PATHS;
  path = READ_PATHS{1};
end

% ---------------------------------------------------------------------------
global PASSED FAILED OUT_BUF ERR_BUF READ_PATHS;
PASSED = 0;
FAILED = 0;

% counts -------------------------------------------------------------------
plain = uint8(sprintf('alpha beta\ngamma delta\n'));
tally = textstat.counts(plain);
check_equal('plain lines', tally.lines, 2);
check_equal('plain words', tally.words, 4);
check_equal('plain bytes', tally.bytes, 23);

single = textstat.counts(uint8('one two three'));
check_equal('no newline lines', single.lines, 0);
check_equal('no newline words', single.words, 3);
check_equal('no newline bytes', single.bytes, 13);

separators = textstat.counts(uint8(sprintf('a\tb\vc\fd\re f\n')));
check_equal('control separators words', separators.words, 6);
check_equal('control separators lines', separators.lines, 1);

empty = textstat.counts(uint8([]));
check_equal('empty lines', empty.lines, 0);
check_equal('empty words', empty.words, 0);
check_equal('empty bytes', empty.bytes, 0);

spaces = textstat.counts(uint8('   '));
check_equal('only spaces words', spaces.words, 0);
check_equal('only spaces bytes', spaces.bytes, 3);

utf8 = textstat.counts(uint8([104 195 169 108 108 111 32 119 195 182 114 108 100 10]));
check_equal('utf8 bytes', utf8.bytes, 14);
check_equal('utf8 words', utf8.words, 2);

characters = textstat.counts(sprintf('alpha beta\ngamma\n'));
check_equal('char input lines', characters.lines, 2);
check_equal('char input bytes', characters.bytes, 17);

left = textstat.counts(uint8(sprintf('alpha\n')));
right = textstat.counts(uint8(sprintf('beta gamma\n')));
summed = textstat.add_counts(left, right);
check_equal('summed lines', summed.lines, 2);
check_equal('summed words', summed.words, 3);
check_equal('summed bytes', summed.bytes, 17);

% options ------------------------------------------------------------------
default = textstat.parse_options({});
check_equal('default status', default.status, 'ok');
check_equal('default figures', [default.lines default.words default.bytes], [true true true]);
check_equal('default files', numel(default.files), 0);

only_words = textstat.parse_options({'-w', 'a.txt'});
check_equal('short flag words', [only_words.lines only_words.words only_words.bytes], [false true false]);
check_equal('short flag file', only_words.files{1}, 'a.txt');

cluster = textstat.parse_options({'-lw'});
check_equal('cluster figures', [cluster.lines cluster.words cluster.bytes], [true true false]);

long_forms = textstat.parse_options({'--bytes', '--lines', 'b.txt'});
check_equal('long figures', [long_forms.lines long_forms.words long_forms.bytes], [true false true]);

terminator = textstat.parse_options({'--', '-l'});
check_equal('terminator figure defaults', [terminator.lines terminator.words terminator.bytes], [true true true]);
check_equal('terminator file', terminator.files{1}, '-l');

dash = textstat.parse_options({'-'});
check_equal('dash is a file', dash.files{1}, '-');

help = textstat.parse_options({'-h'});
check_equal('help short', help.status, 'help');
help = textstat.parse_options({'--help'});
check_equal('help long', help.status, 'help');
version = textstat.parse_options({'-V'});
check_equal('version short', version.status, 'version');
version = textstat.parse_options({'--version'});
check_equal('version long', version.status, 'version');

bogus = textstat.parse_options({'--bogus'});
check_equal('bogus status', bogus.status, 'usage-error');
check_equal('bogus message', bogus.message, 'unknown option: --bogus');
bogus = textstat.parse_options({'-x'});
check_equal('bogus short', bogus.status, 'usage-error');

% runner -------------------------------------------------------------------
sources = struct();
sources.('a.txt') = sprintf('alpha beta\ngamma delta\n');
sources.('b.txt') = 'one two three';

reset_buffers();
io = harness_io(sources, sprintf('alpha beta\ngamma\n'));
code = textstat.run({'a.txt'}, io);
check_equal('run exit', code, 0);
check_equal('run row', OUT_BUF, sprintf(' 2  4 23 a.txt\n'));
check_equal('run read path', only_path(), 'a.txt');

reset_buffers();
io = harness_io(sources, '');
code = textstat.run({'-w', 'a.txt'}, io);
check_equal('run figure row', OUT_BUF, sprintf('4 a.txt\n'));

reset_buffers();
io = harness_io(sources, '');
code = textstat.run({'a.txt', 'b.txt'}, io);
check_equal('run two rows', OUT_BUF, sprintf(' 2  4 23 a.txt\n 0  3 13 b.txt\n 2  7 36 total\n'));
check_equal('run two exit', code, 0);

reset_buffers();
io = harness_io(sources, sprintf('alpha beta\ngamma\n'));
code = textstat.run({}, io);
check_equal('run stdin row', OUT_BUF, sprintf(' 2  3 17 -\n'));
check_equal('run stdin exit', code, 0);

reset_buffers();
io = harness_io(sources, sprintf('alpha beta\ngamma\n'));
code = textstat.run({'-w', '-'}, io);
check_equal('run dash operand', OUT_BUF, sprintf('3 -\n'));

reset_buffers();
io = harness_io(sources, '');
code = textstat.run({'a.txt', 'missing.txt'}, io);
check_equal('run missing exit', code, 1);
check_equal('run missing rows', OUT_BUF, sprintf(' 2  4 23 a.txt\n 2  4 23 total\n'));
check_equal('run missing complaint', ERR_BUF, sprintf('error: cannot open ''missing.txt''\n'));

reset_buffers();
io = harness_io(sources, '');
code = textstat.run({'missing.txt', 'gone.txt'}, io);
check_equal('run all missing exit', code, 1);
check_equal('run all missing rows', OUT_BUF, sprintf('0 0 0 total\n'));

reset_buffers();
io = harness_io(sources, '');
code = textstat.run({'--help'}, io);
check_equal('run help exit', code, 0);
check_equal('run help mentions usage', ~isempty(strfind(OUT_BUF, 'Usage:')), true);

reset_buffers();
io = harness_io(sources, '');
code = textstat.run({'--version'}, io);
check_equal('run version exit', code, 0);
check_equal('run version text', OUT_BUF, sprintf('0.1.0\n'));

reset_buffers();
io = harness_io(sources, '');
code = textstat.run({'--bogus'}, io);
check_equal('run bogus exit', code, 2);
check_equal('run bogus stdout', OUT_BUF, '');
check_equal('run bogus stderr', ERR_BUF, sprintf('%s: unknown option: --bogus\nTry ''%s --help'' for more information.\n', textstat.tool_name(), textstat.tool_name()));

printf('checks: %d, passed: %d, failed: %d\n', PASSED + FAILED, PASSED, FAILED);
if FAILED > 0
  exit(1);
end
exit(0);
