package {{ package_name }};

import java.io.IOException;
import java.io.InputStream;
import java.io.PrintStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

/**
 * The runnable command: turns argv into output and an exit code.
 *
 * <p>Nothing here calls {@code System.exit}, so tests drive {@link #run} directly.
 * Exit codes: {@code 0} success, {@code 1} unreadable input, {@code 2} bad usage.
 */
public final class Cli {

    private static final String PROGRAM = "{{ npm_name }}";

    private final InputStream stdin;

    public Cli(InputStream stdin) {
        this.stdin = stdin;
    }

    public int run(String[] args, PrintStream out, PrintStream err) {
        Options options = Options.parse(args);
        switch (options.status()) {
            case HELP -> {
                out.print(Options.usage(PROGRAM));
                return 0;
            }
            case VERSION -> {
                out.println(Options.VERSION);
                return 0;
            }
            case ERROR -> {
                err.println("error: " + options.error());
                err.println();
                err.print(Options.usage(PROGRAM));
                return 2;
            }
            case OK -> {
                // fall through to counting
            }
        }

        Options.Mode mode = options.mode();
        List<String> files = options.files();
        if (files.isEmpty()) {
            Counts counts;
            try {
                counts = TextStat.count(stdin.readAllBytes());
            } catch (IOException exc) {
                err.println("error: cannot read standard input: " + exc.getMessage());
                return 1;
            }
            print(out, counts, mode, "");
            return 0;
        }

        Counts total = new Counts(0, 0, 0);
        boolean failed = false;
        for (String path : files) {
            Counts counts;
            if (path.equals("-")) {
                try {
                    counts = TextStat.count(stdin.readAllBytes());
                } catch (IOException exc) {
                    err.println("error: cannot read standard input: " + exc.getMessage());
                    failed = true;
                    continue;
                }
                print(out, counts, mode, "");
            } else {
                try {
                    counts = TextStat.count(Files.readAllBytes(Path.of(path)));
                } catch (IOException exc) {
                    err.println("error: cannot open '" + path + "'");
                    failed = true;
                    continue;
                }
                print(out, counts, mode, path);
            }
            total = total.plus(counts);
        }

        if (files.size() > 1) {
            print(out, total, mode, "total");
        }
        return failed ? 1 : 0;
    }

    private static void print(PrintStream out, Counts counts, Options.Mode mode, String label) {
        StringBuilder line = new StringBuilder();
        if (mode == Options.Mode.ALL || mode == Options.Mode.LINES) {
            line.append(String.format("%8d", counts.lines()));
        }
        if (mode == Options.Mode.ALL || mode == Options.Mode.WORDS) {
            line.append(String.format("%8d", counts.words()));
        }
        if (mode == Options.Mode.ALL || mode == Options.Mode.BYTES) {
            line.append(String.format("%8d", counts.bytes()));
        }
        if (!label.isEmpty()) {
            line.append(' ').append(label);
        }
        out.println(line);
    }
}
