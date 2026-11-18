package {{ package_name }};

import java.io.IOException;
import java.io.PrintWriter;
import java.io.Reader;
import java.util.Map;

/** Command line entry point. */
public final class App {

    private static final String USAGE = """
            Usage: runner [options] < document

            Reads text from stdin and prints the most frequent words as
            "word count" lines.

            Options:
              -n, --top N     how many words to print (default 10)
              -w, --word W    print the count of one word instead
              -a, --all       print every distinct word
              -h, --help      show this message
            """;

    private App() {
    }

    public static void main(String[] args) {
        PrintWriter out = new PrintWriter(System.out, true);
        PrintWriter err = new PrintWriter(System.err, true);
        System.exit(run(args, new java.io.InputStreamReader(System.in), out, err));
    }

    public static int run(String[] args, Reader input, PrintWriter out, PrintWriter err) {
        int top = 10;
        String query = null;
        boolean all = false;

        for (int index = 0; index < args.length; index++) {
            String argument = args[index];
            switch (argument) {
                case "-n", "--top" -> {
                    if (index + 1 >= args.length) {
                        return usage(err, argument + " needs a number");
                    }
                    try {
                        top = Integer.parseInt(args[++index]);
                    } catch (NumberFormatException error) {
                        return usage(err, "not a number: " + args[index]);
                    }
                    if (top < 1) {
                        return usage(err, "top must be at least 1");
                    }
                }
                case "-w", "--word" -> {
                    if (index + 1 >= args.length) {
                        return usage(err, argument + " needs a word");
                    }
                    query = args[++index];
                }
                case "-a", "--all" -> all = true;
                case "-h", "--help" -> {
                    out.print(USAGE);
                    return 0;
                }
                default -> {
                    return usage(err, "unknown option " + argument);
                }
            }
        }

        String text;
        try {
            text = read(input);
        } catch (IOException error) {
            err.println("wordcount: cannot read stdin: " + error.getMessage());
            return 1;
        }

        WordCount counter = WordCount.of(text);
        if (query != null) {
            out.println(query + " " + counter.count(query));
            return 0;
        }
        int limit = all ? (int) counter.distinct() : top;
        for (Map.Entry<String, Long> entry : counter.top(limit)) {
            out.println(entry.getKey() + " " + entry.getValue());
        }
        return 0;
    }

    private static int usage(PrintWriter err, String problem) {
        err.println("wordcount: " + problem);
        err.print(USAGE);
        return 2;
    }

    private static String read(Reader input) throws IOException {
        StringBuilder builder = new StringBuilder();
        char[] buffer = new char[4096];
        int read;
        while ((read = input.read(buffer)) != -1) {
            builder.append(buffer, 0, read);
        }
        return builder.toString();
    }
}
