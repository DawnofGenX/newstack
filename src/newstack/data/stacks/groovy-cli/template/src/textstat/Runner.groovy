package textstat

/**
 * Everything the CLI decides, with the four side effects handed in as closures:
 * reading a file, reading standard input, writing to stdout, writing to stderr.
 */
class Runner {
    String program = '{{ npm_name }}'

    Closure<byte[]> readFile
    Closure<byte[]> readStdin
    Closure<String> out
    Closure<String> err

    int run(List<String> args) {
        Options options = Options.parse(args)

        if (options.status == 'help') {
            out(Options.usage(program))
            return 0
        }
        if (options.status == 'version') {
            out(Options.VERSION + '\n')
            return 0
        }
        if (options.status == 'usage-error') {
            err("${program}: ${options.message}\n")
            err("Try '${program} --help' for more information.\n")
            return 2
        }

        boolean implicit = options.files.isEmpty()
        List<String> operands = implicit ? (['-'] as List) : options.files
        boolean pipe = false
        boolean failed = false
        List<Map> rows = []
        Counts total = Counts.empty()

        for (String path : operands) {
            byte[] data = readOne(path)
            if (data == null) {
                err("error: cannot open '${path}'\n")
                failed = true
                continue
            }
            if (path == '-') {
                // wc pads to its widest cell whenever a pipe is involved.
                pipe = true
            }
            Counts counts = Counts.of(data)
            total = total.plus(counts)
            rows << [label: implicit ? '' : path, counts: counts]
        }

        int width = widthFor(options.figures, rows, pipe, total.bytes)
        for (Map row : rows) {
            String cells = cellsFor(options.figures, (Counts) row.counts, width)
            String label = (String) row.label
            out(label ? "${cells} ${label}\n" : "${cells}\n")
        }
        if (operands.size() > 1) {
            out("${cellsFor(options.figures, total, width)} total\n")
        }

        return failed ? 1 : 0
    }

    private byte[] readOne(String path) {
        try {
            return path == '-' ? (byte[]) readStdin() : (byte[]) readFile(path)
        } catch (Exception ignored) {
            return null
        }
    }

    // wc's padding, copied rather than guessed: one figure for one readable
    // operand is printed at its natural width; anything that involved a pipe
    // gets the widest cell wc ever needs; otherwise the width is the digit
    // count of the total byte count.
    private static int widthFor(List<String> figures, List<Map> rows, boolean pipe, long totalBytes) {
        if (figures.size() == 1 && rows.size() <= 1) {
            if (rows.isEmpty()) {
                return 1
            }
            Counts counts = (Counts) rows.get(0).counts
            return Math.max(1, String.valueOf(counts.figure(figures.get(0))).length())
        }
        if (pipe) {
            return 7
        }
        return Math.max(1, String.valueOf(totalBytes).length())
    }

    private static String cellsFor(List<String> figures, Counts counts, int width) {
        return figures.collect { String name ->
            String.format("%${width}d", (Object) Long.valueOf(counts.figure(name)))
        }.join(' ')
    }
}
