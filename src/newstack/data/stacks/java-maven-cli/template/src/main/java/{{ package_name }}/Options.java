package {{ package_name }};

import java.util.ArrayList;
import java.util.List;

/** Parsed command line: the chosen mode, the files, and how parsing ended. */
public final class Options {

    public static final String VERSION = "0.1.0";

    /** Which figures to print; {@code ALL} prints lines, words and bytes. */
    public enum Mode {
        ALL,
        LINES,
        WORDS,
        BYTES
    }

    /** How argument parsing ended. */
    public enum Status {
        OK,
        HELP,
        VERSION,
        ERROR
    }

    private final Mode mode;
    private final List<String> files;
    private final Status status;
    private final String error;

    private Options(Mode mode, List<String> files, Status status, String error) {
        this.mode = mode;
        this.files = List.copyOf(files);
        this.status = status;
        this.error = error;
    }

    public Mode mode() {
        return mode;
    }

    public List<String> files() {
        return files;
    }

    public Status status() {
        return status;
    }

    public String error() {
        return error;
    }

    /** Hand-rolled parser: no dependency, and every branch is unit tested. */
    public static Options parse(String[] args) {
        Mode chosen = null;
        boolean onlyFiles = false;
        List<String> files = new ArrayList<>();

        for (String arg : args) {
            if (onlyFiles || arg.isEmpty() || arg.equals("-")) {
                files.add(arg);
                continue;
            }
            if (arg.equals("--")) {
                onlyFiles = true;
                continue;
            }
            if (arg.equals("-h") || arg.equals("--help")) {
                return new Options(chosenOrAll(chosen), files, Status.HELP, "");
            }
            if (arg.equals("-V") || arg.equals("--version")) {
                return new Options(chosenOrAll(chosen), files, Status.VERSION, "");
            }
            Mode requested = modeFor(arg);
            if (requested != null) {
                if (chosen != null && chosen != requested) {
                    return new Options(
                            chosen,
                            files,
                            Status.ERROR,
                            "choose one of -l, -w, -c: '" + arg + "' conflicts with an earlier mode");
                }
                chosen = requested;
                continue;
            }
            if (arg.startsWith("-")) {
                return new Options(
                        chosenOrAll(chosen),
                        files,
                        Status.ERROR,
                        "unknown option '" + arg + "'");
            }
            files.add(arg);
        }
        return new Options(chosenOrAll(chosen), files, Status.OK, "");
    }

    private static Mode chosenOrAll(Mode chosen) {
        return chosen == null ? Mode.ALL : chosen;
    }

    private static Mode modeFor(String arg) {
        return switch (arg) {
            case "-l", "--lines" -> Mode.LINES;
            case "-w", "--words" -> Mode.WORDS;
            case "-c", "--bytes" -> Mode.BYTES;
            default -> null;
        };
    }

    /** Help text; the program name comes from the artifact so it matches the jar. */
    public static String usage(String program) {
        return "usage: " + program + " [-l | -w | -c] [--] [FILE ...]\n"
                + "\n"
                + "Count lines, words and bytes in each FILE, or in standard input\n"
                + "when no FILE is given. With more than one FILE a total is printed.\n"
                + "\n"
                + "  -l, --lines     print the line count only\n"
                + "  -w, --words     print the word count only\n"
                + "  -c, --bytes     print the byte count only\n"
                + "  -h, --help      show this help and exit\n"
                + "  -V, --version   show the version and exit\n";
    }
}
