package {{ package_name }};

import java.io.BufferedReader;
import java.io.IOException;
import java.io.Reader;
import java.io.PrintWriter;
import java.util.Optional;

/** Command line front end: reads a trace of cache commands and prints results. */
public final class App {

    private App() {
    }

    public static void main(String[] args) {
        PrintWriter out = new PrintWriter(System.out, true);
        PrintWriter err = new PrintWriter(System.err, true);
        int status = run(args, new java.io.InputStreamReader(System.in), out, err);
        out.flush();
        err.flush();
        System.exit(status);
    }

    /** Runs the CLI with injected streams so tests never touch the process. */
    public static int run(String[] args, Reader input, PrintWriter out, PrintWriter err) {
        int capacity = 3;
        for (int index = 0; index < args.length; index++) {
            String argument = args[index];
            if (argument.equals("-h") || argument.equals("--help")) {
                out.println(usage());
                return 0;
            }
            if (argument.equals("-c") || argument.equals("--capacity")) {
                if (index + 1 >= args.length) {
                    err.println("option " + argument + " needs a value");
                    return 2;
                }
                index++;
                try {
                    capacity = Integer.parseInt(args[index]);
                } catch (NumberFormatException error) {
                    err.println("capacity must be a number: " + args[index]);
                    return 2;
                }
                continue;
            }
            err.println("unknown argument: " + argument);
            err.println(usage());
            return 2;
        }

        LruCache<String, String> cache;
        try {
            cache = new LruCache<>(capacity);
        } catch (IllegalArgumentException error) {
            err.println(error.getMessage());
            return 2;
        }

        BufferedReader reader = new BufferedReader(input);
        int lineNumber = 0;
        try {
            String line;
            while ((line = reader.readLine()) != null) {
                lineNumber++;
                String trimmed = line.trim();
                if (trimmed.isEmpty() || trimmed.startsWith("#")) {
                    continue;
                }
                if (!apply(cache, trimmed, out, err)) {
                    err.println("line " + lineNumber + ": " + trimmed);
                    return 1;
                }
            }
        } catch (IOException error) {
            err.println("cannot read input: " + error.getMessage());
            return 1;
        }
        return 0;
    }

    private static boolean apply(LruCache<String, String> cache, String line, PrintWriter out,
            PrintWriter err) {
        String[] parts = line.split("\\s+");
        String command = parts[0].toUpperCase();
        switch (command) {
            case "PUT" -> {
                if (parts.length != 3) {
                    err.println("PUT needs a key and a value");
                    return false;
                }
                Optional<String> evicted = cache.put(parts[1], parts[2]);
                out.println("PUT " + parts[1] + " size=" + cache.size()
                        + evicted.map(key -> " evicted=" + key).orElse(""));
                return true;
            }
            case "GET" -> {
                if (parts.length != 2) {
                    err.println("GET needs a key");
                    return false;
                }
                Optional<String> value = cache.get(parts[1]);
                out.println(value.isPresent()
                        ? "GET " + parts[1] + " -> " + value.get() + " (hit)"
                        : "GET " + parts[1] + " -> miss");
                return true;
            }
            case "PEEK" -> {
                if (parts.length != 2) {
                    err.println("PEEK needs a key");
                    return false;
                }
                Optional<String> value = cache.peek(parts[1]);
                out.println(value.isPresent()
                        ? "PEEK " + parts[1] + " -> " + value.get()
                        : "PEEK " + parts[1] + " -> absent");
                return true;
            }
            case "DEL" -> {
                if (parts.length != 2) {
                    err.println("DEL needs a key");
                    return false;
                }
                out.println("DEL " + parts[1] + " removed=" + cache.remove(parts[1]));
                return true;
            }
            case "KEYS" -> {
                out.println("KEYS " + String.join(" ", cache.keys()));
                return true;
            }
            case "STATS" -> {
                LruCache.Stats stats = cache.stats();
                out.println("STATS hits=" + stats.hits() + " misses=" + stats.misses()
                        + " evictions=" + stats.evictions() + " size=" + stats.size()
                        + "/" + stats.capacity()
                        + String.format(java.util.Locale.ROOT, " hitRate=%.2f", stats.hitRate()));
                return true;
            }
            case "CLEAR" -> {
                cache.clear();
                out.println("CLEAR size=0");
                return true;
            }
            case "QUIT" -> {
                return true;
            }
            default -> {
                err.println("unknown command: " + parts[0]);
                return false;
            }
        }
    }

    static String usage() {
        return "usage: {{ npm_name }} [-c N] [FILE]\n\n"
                + "Reads a trace from stdin:\n"
                + "  PUT key value\n  GET key\n  PEEK key\n  DEL key\n"
                + "  KEYS\n  STATS\n  CLEAR\n  QUIT\n"
                + "Exit status is 1 for a bad trace line and 2 for a bad invocation.";
    }
}
