/// argv parsing with no side effects: clusters, long forms and "--".
module options;

enum Status {
    ok,
    help,
    version_,
    usageError,
}

struct Options {
    bool lines;
    bool words;
    bool bytes;
    string[] operands;
}

struct ParseResult {
    Status status;
    Options options;
    string message;
}

enum toolVersion = "0.1.0";

string usage(string program) {
    return "Usage: " ~ program ~ " [OPTION]... [FILE]...\n"
        ~ "Print newline, word, and byte counts for each FILE.\n"
        ~ "With no FILE, or when FILE is -, read standard input.\n\n"
        ~ "  -l, --lines   print the newline counts\n"
        ~ "  -w, --words   print the word counts\n"
        ~ "  -c, --bytes   print the byte counts\n"
        ~ "  -h, --help    display this help and exit\n"
        ~ "      --version  output version information and exit\n";
}

private bool setFlag(ref Options options, char ch) {
    switch (ch) {
    case 'l':
        options.lines = true;
        return true;
    case 'w':
        options.words = true;
        return true;
    case 'c':
        options.bytes = true;
        return true;
    default:
        return false;
    }
}

ParseResult parse(string[] argv) {
    Options options;
    bool onlyOperands = false;

    foreach (arg; argv) {
        if (onlyOperands || arg == "-" || arg.length == 0 || arg[0] != '-') {
            options.operands ~= arg;
        } else if (arg == "--") {
            onlyOperands = true;
        } else if (arg == "--help" || arg == "-h") {
            return ParseResult(Status.help, options, "");
        } else if (arg == "--version") {
            return ParseResult(Status.version_, options, "");
        } else if (arg.length > 2 && arg[0..2] == "--") {
            if (arg == "--lines") {
                options.lines = true;
            } else if (arg == "--words") {
                options.words = true;
            } else if (arg == "--bytes") {
                options.bytes = true;
            } else {
                return ParseResult(Status.usageError, options, "unrecognized option: " ~ arg);
            }
        } else {
            foreach (ch; arg[1..$]) {
                if (!setFlag(options, ch)) {
                    return ParseResult(Status.usageError, options,
                        "invalid option -- " ~ [ch].idup);
                }
            }
        }
    }

    if (!options.lines && !options.words && !options.bytes) {
        options.lines = true;
        options.words = true;
        options.bytes = true;
    }

    return ParseResult(Status.ok, options, "");
}
