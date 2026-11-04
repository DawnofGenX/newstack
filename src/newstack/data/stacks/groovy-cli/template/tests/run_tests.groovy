// Runs every suite and reports one tally. No framework, no network, no disk.
import textstat.Counts
import textstat.Options
import textstat.Runner

byte[] bytesOf(String text) {
    return text.getBytes('UTF-8')
}

void countsSuite(String program) {
    Counts empty = Counts.of(new byte[0])
    Harness.checkEqual('empty: lines', empty.lines, 0L)
    Harness.checkEqual('empty: words', empty.words, 0L)
    Harness.checkEqual('empty: bytes', empty.bytes, 0L)

    Counts plain = Counts.of(bytesOf("alpha beta\ngamma delta\n"))
    Harness.checkEqual('plain: lines', plain.lines, 2L)
    Harness.checkEqual('plain: words', plain.words, 4L)
    Harness.checkEqual('plain: bytes', plain.bytes, 23L)

    Counts noNewline = Counts.of(bytesOf('alpha beta\ngamma'))
    Harness.checkEqual('no trailing newline: lines', noNewline.lines, 1L)
    Harness.checkEqual('no trailing newline: words', noNewline.words, 3L)
    Harness.checkEqual('no trailing newline: bytes', noNewline.bytes, 16L)

    Counts utf8 = Counts.of(bytesOf('h\u00e9llo w\u00f6rld\n'))
    Harness.checkEqual('utf-8: words', utf8.words, 2L)
    Harness.checkEqual('utf-8: bytes counts utf-8 bytes', utf8.bytes, 14L)

    Counts control = Counts.of(bytesOf('a\tb' + (11 as char) + 'c' + (12 as char) + 'd\n'))
    Harness.checkEqual('vertical tab and form feed separate words', control.words, 4L)
    Harness.checkEqual('control: lines', control.lines, 1L)
    Harness.checkEqual('control: bytes', control.bytes, 8L)

    Counts cr = Counts.of(bytesOf("alpha beta\rgamma\n"))
    Harness.checkEqual('carriage return separates words', cr.words, 3L)
    Harness.checkEqual('carriage return is not a newline', cr.lines, 1L)

    Counts sum = plain.plus(noNewline)
    Harness.checkEqual('add: lines', sum.lines, 3L)
    Harness.checkEqual('add: words', sum.words, 7L)
    Harness.checkEqual('add: bytes', sum.bytes, 39L)

    Harness.checkEqual('columns follow the figures', plain.columns(['lines', 'bytes']), [2L, 23L])
    Harness.checkEqual('figure lookup by name', plain.figure('words'), 4L)
    Harness.checkEqual('whitespace set covers six bytes', Counts.WHITESPACE, [32, 9, 10, 13, 11, 12])
}

void optionsSuite(String program) {
    Options all = Options.parse([])
    Harness.checkEqual('no flags means every figure', all.figures, ['lines', 'words', 'bytes'])
    Harness.checkEqual('no flags: status', all.status, 'ok')
    Harness.checkEqual('no flags: no files', all.files, [])

    Options shortFlags = Options.parse(['-l', '-c', 'a.txt'])
    Harness.checkEqual('short flags', shortFlags.figures, ['lines', 'bytes'])
    Harness.checkEqual('short flags: files', shortFlags.files, ['a.txt'])

    Options cluster = Options.parse(['-lwc'])
    Harness.checkEqual('a cluster expands', cluster.figures, ['lines', 'words', 'bytes'])

    Options reversed = Options.parse(['-c', '-l'])
    Harness.checkEqual('wc prints figures in its own order', reversed.figures, ['lines', 'bytes'])

    Options longFlags = Options.parse(['--words', 'x.txt'])
    Harness.checkEqual('long flags', longFlags.figures, ['words'])

    Options dash = Options.parse(['-'])
    Harness.checkEqual('a lone dash is a file', dash.files, ['-'])

    Options terminator = Options.parse(['--', '-l'])
    Harness.checkEqual('after -- everything is a file', terminator.files, ['-l'])
    Harness.checkEqual('after -- no figure flag was read', terminator.figures, ['lines', 'words', 'bytes'])

    Harness.checkEqual('help short-circuits', Options.parse(['-h', 'a.txt']).status, 'help')
    Harness.checkEqual('version short-circuits', Options.parse(['--version']).status, 'version')
    Options wrong = Options.parse(['--bogus'])
    Harness.checkEqual('unknown option: status', wrong.status, 'usage-error')
    Harness.checkEqual('unknown option: message', wrong.message, 'unknown option: --bogus')
    Harness.checkEqual('unknown short option', Options.parse(['-x']).message, 'unknown option: -x')

    Harness.check('usage names the program', Options.usage(program).contains("Usage: ${program} [OPTION]... [FILE]..."))
    Harness.check('usage explains standard input', Options.usage(program).contains('read standard input'))
    Harness.checkEqual('version constant', Options.VERSION, '0.1.0')
}

void runnerSuite(String program) {
    byte[] plain = bytesOf("alpha beta\ngamma delta\n")
    byte[] shorter = bytesOf('alpha beta\ngamma')
    Map<String, byte[]> files = [:] as LinkedHashMap
    files['p1.txt'] = plain
    files['p2.txt'] = shorter
    files['empty.txt'] = new byte[0]

    def runCase = { String name, List<String> args, byte[] stdin, String wantOut, String wantErr, int wantCode ->
        Harness.clearBuffers()
        Runner runner = new Runner(
            program: program,
            readFile: { String path ->
                if (!files.containsKey(path)) {
                    throw new FileNotFoundException("no such file: ${path}")
                }
                return files[path]
            },
            readStdin: { -> stdin },
            out: { String text -> Harness.out(text); return null },
            err: { String text -> Harness.err(text); return null },
        )
        int code = runner.run(args)
        Harness.checkEqual("${name}: exit code", code, wantCode)
        Harness.checkText("${name}: stdout", Harness.outText(), wantOut)
        Harness.checkText("${name}: stderr", Harness.errText(), wantErr)
    }

    runCase('one file, three figures', ['p1.txt'], plain, ' 2  4 23 p1.txt\n', '', 0)
    runCase('one figure from one file is not padded', ['-l', 'p1.txt'], plain, '2 p1.txt\n', '', 0)
    runCase('two figures share one width', ['-l', '-w', 'p1.txt'], plain, ' 2  4 p1.txt\n', '', 0)
    runCase('two files get a total row', ['p1.txt', 'p2.txt'], plain,
        ' 2  4 23 p1.txt\n 1  3 16 p2.txt\n 3  7 39 total\n', '', 0)
    runCase('one figure over two files is still padded', ['-l', 'p1.txt', 'p2.txt'], plain,
        ' 2 p1.txt\n 1 p2.txt\n 3 total\n', '', 0)
    runCase('an unreadable file is reported and the total survives', ['p1.txt', 'gone.txt'], plain,
        ' 2  4 23 p1.txt\n 2  4 23 total\n', "error: cannot open 'gone.txt'\n", 1)
    runCase('no operand reads standard input without a label', [], plain,
        '      2       4      23\n', '', 0)
    runCase('an explicit dash is labelled', ['-w', '-'], plain, '4 -\n', '', 0)
    runCase('a pipe widens every cell', ['-l', '-w'], plain, '      2       4\n', '', 0)
    runCase('help goes to stdout', ['--help'], plain, Options.usage(program), '', 0)
    runCase('version goes to stdout', ['--version'], plain, "0.1.0\n", '', 0)
    runCase('an unknown option is refused', ['--bogus'], plain, '',
        "${program}: unknown option: --bogus\nTry '${program} --help' for more information.\n", 2)
    runCase('an empty file counts nothing', ['empty.txt'], plain, '0 0 0 empty.txt\n', '', 0)
    runCase('a missing file alone still fails', ['gone.txt'], plain, '',
        "error: cannot open 'gone.txt'\n", 1)
}

String program = new Runner().program

Harness.resetAll()
countsSuite(program)
optionsSuite(program)
runnerSuite(program)
System.exit(Harness.report())
