# The argv parser. It walks ARGV by hand and never lets awk open a file: the
# runner reads every operand itself, so a name with a space or a leading dash
# is just a string here.

function tool_version() {
    return "0.1.0"
}

function usage(program) {
    return "Usage: " program " [OPTION]... [FILE]...\n" \
           "\n" \
           "Print newline, word, and byte counts for each FILE.\n" \
           "\n" \
           "  -l, --lines    print the newline counts\n" \
           "  -w, --words    print the word counts\n" \
           "  -c, --bytes    print the byte counts\n" \
           "  -h, --help     show this help and exit\n" \
           "  -V, --version  show the version and exit\n" \
           "\n" \
           "With no FILE, or when FILE is -, read standard input.\n"
}

# Reads ARGV[1] .. ARGV[ARGC-1] into OPT_*. Sets OPT_STATUS to ok, help,
# version or usage-error.
function options_parse(   i, arg, position, letter, literal) {
    OPT_STATUS = "ok"
    OPT_MESSAGE = ""
    OPT_SHOW_L = 0
    OPT_SHOW_W = 0
    OPT_SHOW_C = 0
    OPT_ANY_FIGURE = 0
    OPT_NFILES = 0
    literal = 0

    for (i = 1; i < ARGC; i++) {
        arg = ARGV[i]

        if (!literal && arg == "--") {
            literal = 1
            continue
        }

        if (!literal && substr(arg, 1, 2) == "--") {
            if (arg == "--lines") {
                OPT_SHOW_L = 1
                OPT_ANY_FIGURE = 1
            } else if (arg == "--words") {
                OPT_SHOW_W = 1
                OPT_ANY_FIGURE = 1
            } else if (arg == "--bytes") {
                OPT_SHOW_C = 1
                OPT_ANY_FIGURE = 1
            } else if (arg == "--help") {
                OPT_STATUS = "help"
                return
            } else if (arg == "--version") {
                OPT_STATUS = "version"
                return
            } else {
                OPT_STATUS = "usage-error"
                OPT_MESSAGE = "unknown option: " arg
                return
            }
            continue
        }

        if (!literal && length(arg) > 1 && substr(arg, 1, 1) == "-") {
            for (position = 2; position <= length(arg); position++) {
                letter = substr(arg, position, 1)
                if (letter == "l") {
                    OPT_SHOW_L = 1
                    OPT_ANY_FIGURE = 1
                } else if (letter == "w") {
                    OPT_SHOW_W = 1
                    OPT_ANY_FIGURE = 1
                } else if (letter == "c") {
                    OPT_SHOW_C = 1
                    OPT_ANY_FIGURE = 1
                } else if (letter == "h") {
                    OPT_STATUS = "help"
                    return
                } else if (letter == "V") {
                    OPT_STATUS = "version"
                    return
                } else {
                    OPT_STATUS = "usage-error"
                    OPT_MESSAGE = "unknown option: -" letter
                    return
                }
            }
            continue
        }

        OPT_FILES[++OPT_NFILES] = arg
    }

    if (!OPT_ANY_FIGURE) {
        OPT_SHOW_L = 1
        OPT_SHOW_W = 1
        OPT_SHOW_C = 1
    }
}

# The figures in the order wc prints them, whatever the flag order was.
function options_figures(order,   n) {
    n = 0
    if (OPT_SHOW_L) {
        order[++n] = "lines"
    }
    if (OPT_SHOW_W) {
        order[++n] = "words"
    }
    if (OPT_SHOW_C) {
        order[++n] = "bytes"
    }
    return n
}
