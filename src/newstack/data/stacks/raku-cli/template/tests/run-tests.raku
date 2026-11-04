# Runs every suite and reports one tally. No framework, no network, no disk.
use Harness;
use Textstat::Counts;
use Textstat::Options;
use Textstat::Runner;

sub bytes(Str $text --> Buf) { $text.encode('utf-8').Buf }

sub counts-suite() {
    my $empty = counts-of(Buf.new);
    my $plain = counts-of(bytes("alpha beta\ngamma delta\n"));
    my $no-newline = counts-of(bytes("alpha beta\ngamma"));
    my $multi = counts-of(bytes("h\x[e9]llo w\x[f6]rld\n"));
    my $control = counts-of(bytes("a\tb\x[0b]c\x[0c]d\n"));
    my $spaces = counts-of(bytes(" \t\n"));

    check-equal 'empty: lines', $empty.lines, 0;
    check-equal 'empty: words', $empty.words, 0;
    check-equal 'empty: bytes', $empty.bytes, 0;
    check-equal 'plain: lines', $plain.lines, 2;
    check-equal 'plain: words', $plain.words, 4;
    check-equal 'plain: bytes', $plain.bytes, 23;
    check-equal 'no trailing newline: lines', $no-newline.lines, 1;
    check-equal 'no trailing newline: words', $no-newline.words, 3;
    check-equal 'no trailing newline: bytes', $no-newline.bytes, 16;
    check-equal 'multibyte: lines', $multi.lines, 1;
    check-equal 'multibyte: words', $multi.words, 2;
    check-equal 'multibyte: bytes', $multi.bytes, 14;
    check-equal 'control: lines', $control.lines, 1;
    check-equal 'control: words', $control.words, 4;
    check-equal 'control: bytes', $control.bytes, 8;
    check-equal 'whitespace only: lines', $spaces.lines, 1;
    check-equal 'whitespace only: words', $spaces.words, 0;
    check-equal 'whitespace only: bytes', $spaces.bytes, 3;

    my $sum = counts-add($plain, $plain);
    check-equal 'add: lines', $sum.lines, 4;
    check-equal 'add: words', $sum.words, 8;
    check-equal 'add: bytes', $sum.bytes, 46;

    check-equal 'columns keep wc order', counts-columns(('lines', 'words', 'bytes'), $plain), (2, 4, 23);
    check-equal 'columns honour the order asked', counts-columns(('bytes', 'lines'), $plain), (23, 2);
}

sub options-suite() {
    check-equal 'no arguments defaults to every figure',
        parse-args(()).figures, ('lines', 'words', 'bytes');
    check-equal 'no arguments collects no files', parse-args(()).files, ();
    check-equal 'short flag', parse-args(('-l',)).figures, ('lines',);
    check-equal 'clustered short flags keep wc order', parse-args(('-cl',)).figures, ('lines', 'bytes');
    check-equal 'repeated short flags collapse', parse-args(('-l', '-l')).figures, ('lines',);
    check-equal 'long flag', parse-args(('--words',)).figures, ('words',);
    check-equal 'files keep their order', parse-args(('a.txt', 'b.txt')).files, ('a.txt', 'b.txt');
    check-equal 'a lone dash is a file', parse-args(('-',)).files, ('-',);
    check-equal 'a dash after a flag is still a file', parse-args(('-w', '-')).files, ('-',);
    check-equal 'double dash ends the flags', parse-args(('--', '-l')).files, ('-l',);
    check-equal 'double dash without flags keeps the defaults',
        parse-args(('--', '-l')).figures, ('lines', 'words', 'bytes');
    check-equal 'help status', parse-args(('--help',)).status, 'help';
    check-equal 'short help status', parse-args(('-h',)).status, 'help';
    check-equal 'version status', parse-args(('-V',)).status, 'version';
    check-equal 'long version status', parse-args(('--version',)).status, 'version';
    check-equal 'unknown long option is refused', parse-args(('--bogus',)).status, 'usage-error';
    check-text 'unknown long option names itself',
        parse-args(('--bogus',)).message, 'unknown option: --bogus';
    check-equal 'unknown short option is refused', parse-args(('-x',)).status, 'usage-error';
    check-text 'unknown short option names itself', parse-args(('-x',)).message, 'unknown option: -x';
    check-equal 'unknown letter in a cluster is refused', parse-args(('-lx',)).status, 'usage-error';
    check-text 'version string', VERSION, '0.1.0';
    my $text = usage('prog');
    check 'usage names the program', $text.contains('Usage: prog [OPTION]... [FILE]...');
    check 'usage explains standard input', $text.contains('read standard input');
}

sub runner-suite() {
    my $plain = bytes("alpha beta\ngamma delta\n");
    my $shorter = bytes("alpha beta\ngamma");
    my %files = 'p1.txt' => $plain, 'p2.txt' => $shorter, 'empty.txt' => Buf.new;

    sub run-case(Str $name, @args, Buf $stdin, Str $want-out, Str $want-err, Int $want-code) {
        clear-buffers();
        my &read-file = -> Str $path {
            die "no such file: $path" unless %files{$path}.defined;
            %files{$path};
        };
        my &read-stdin = -> { $stdin };
        my Int $code = run(@args, &read-file, &read-stdin, &collect-out, &collect-err);
        check-equal "$name: exit code", $code, $want-code;
        check-text "$name: stdout", out-text(), $want-out;
        check-text "$name: stderr", err-text(), $want-err;
    }

    run-case 'one file, three figures', ('p1.txt',), $plain,
        " 2  4 23 p1.txt\n", '', 0;
    run-case 'one file, one figure is not padded', ('-l', 'p1.txt'), $plain,
        "2 p1.txt\n", '', 0;
    run-case 'two figures share one width', ('-l', '-w', 'p1.txt'), $plain,
        " 2  4 p1.txt\n", '', 0;
    run-case 'two files get a total row', ('p1.txt', 'p2.txt'), $plain,
        " 2  4 23 p1.txt\n 1  3 16 p2.txt\n 3  7 39 total\n", '', 0;
    run-case 'an unreadable file is reported and the total survives', ('p1.txt', 'gone.txt'), $plain,
        " 2  4 23 p1.txt\n 2  4 23 total\n", "error: cannot open 'gone.txt'\n", 1;
    run-case 'no operand reads standard input without a label', (), $plain,
        "      2       4      23\n", '', 0;
    run-case 'an explicit dash is labelled', ('-w', '-'), $plain,
        "4 -\n", '', 0;
    run-case 'a pipe widens every cell', ('-l', '-w'), $plain,
        "      2       4\n", '', 0;
    run-case 'help goes to stdout', ('--help',), $plain,
        usage(program-name()), '', 0;
    run-case 'version goes to stdout', ('--version',), $plain, "0.1.0\n", '', 0;
    run-case 'an unknown option is refused', ('--bogus',), $plain, '',
        '{{ npm_name }}' ~ ": unknown option: --bogus\nTry '{{ npm_name }} --help' for more information.\n", 2;
    run-case 'an empty file counts nothing', ('empty.txt',), $plain,
        "0 0 0 empty.txt\n", '', 0;
}

reset-all();
counts-suite();
options-suite();
runner-suite();
exit(report());
