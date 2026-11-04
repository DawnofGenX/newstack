# Everything the CLI decides. The reading, the padding and the messages all
# live here; main.awk only prints what this file builds, so the suite can drive
# the whole thing in-process.

# One read that returns every byte of `path`. RS is "\0", so the whole file
# arrives as a single record; the cost is that a file containing a NUL byte
# would be split, which wc would count as one more byte in the middle.
function read_all(path,   chunk, status, data) {
    data = ""
    READ_FAILED = 0

    if (path == "-") {
        # A bare `getline` would walk ARGV and try to open a flag as a file, so
        # the standard input is named explicitly.
        while ((getline chunk < "/dev/stdin") > 0) {
            data = data chunk
        }
        close("/dev/stdin")
        return data
    }

    status = (getline chunk < path)
    if (status < 0) {
        READ_FAILED = 1
        close(path)
        return ""
    }
    while (status > 0) {
        data = data chunk
        status = (getline chunk < path)
    }
    close(path)
    return data
}

# A right-aligned cell: awk's %*d takes the width from an argument.
function cell(value, width) {
    return sprintf("%*d", width, value)
}

function cells_for(figures, count, width, l, w, b,   text, slot, number) {
    text = ""
    for (slot = 1; slot <= count; slot++) {
        if (figures[slot] == "lines") {
            number = l
        } else if (figures[slot] == "words") {
            number = w
        } else {
            number = b
        }
        text = text (slot > 1 ? " " : "") cell(number, width)
    }
    return text
}

# wc's padding, copied rather than guessed: one figure for one readable operand
# is printed at its natural width; anything that involved a pipe gets the widest
# cell wc ever needs; otherwise the width is the digit count of the total byte
# count.
function width_for(figures, count, rows, pipe, total_bytes,   digits) {
    if (count == 1 && rows <= 1) {
        if (rows == 0) {
            return 1
        }
        if (figures[1] == "lines") {
            digits = length(ROW_LINES[1] "")
        } else if (figures[1] == "words") {
            digits = length(ROW_WORDS[1] "")
        } else {
            digits = length(ROW_BYTES[1] "")
        }
        return (digits < 1 ? 1 : digits)
    }
    if (pipe) {
        return 7
    }
    digits = length(total_bytes "")
    return (digits < 1 ? 1 : digits)
}

# Fills OUT_TEXT, ERR_TEXT and EXIT_CODE. Sets nothing else.
function report_build(   i, path, data, implicit, pipe, failed, rows, figures, count, width, total_l, total_w, total_b, label) {
    OUT_TEXT = ""
    ERR_TEXT = ""
    EXIT_CODE = 0

    options_parse()

    if (OPT_STATUS == "help") {
        OUT_TEXT = usage(PROGRAM_NAME)
        return
    }
    if (OPT_STATUS == "version") {
        OUT_TEXT = tool_version() "\n"
        return
    }
    if (OPT_STATUS == "usage-error") {
        ERR_TEXT = PROGRAM_NAME ": " OPT_MESSAGE "\n" \
                   "Try '" PROGRAM_NAME " --help' for more information.\n"
        EXIT_CODE = 2
        return
    }

    implicit = (OPT_NFILES == 0)
    if (implicit) {
        OPT_FILES[1] = "-"
        OPT_NFILES = 1
    }

    pipe = 0
    failed = 0
    rows = 0
    total_l = 0
    total_w = 0
    total_b = 0

    for (i = 1; i <= OPT_NFILES; i++) {
        path = OPT_FILES[i]
        data = read_all(path)
        if (READ_FAILED) {
            ERR_TEXT = ERR_TEXT "error: cannot open '" path "'\n"
            failed = 1
            continue
        }
        if (path == "-") {
            pipe = 1
        }
        counts_of(data)
        rows++
        ROW_LABEL[rows] = (implicit ? "" : path)
        ROW_LINES[rows] = COUNT_LINES
        ROW_WORDS[rows] = COUNT_WORDS
        ROW_BYTES[rows] = COUNT_BYTES
        total_l += COUNT_LINES
        total_w += COUNT_WORDS
        total_b += COUNT_BYTES
    }

    count = options_figures(figures)
    width = width_for(figures, count, rows, pipe, total_b)

    for (i = 1; i <= rows; i++) {
        label = ROW_LABEL[i]
        OUT_TEXT = OUT_TEXT cells_for(figures, count, width, ROW_LINES[i], ROW_WORDS[i], ROW_BYTES[i])
        if (label != "") {
            OUT_TEXT = OUT_TEXT " " label
        }
        OUT_TEXT = OUT_TEXT "\n"
    }

    if (OPT_NFILES > 1) {
        OUT_TEXT = OUT_TEXT cells_for(figures, count, width, total_l, total_w, total_b) " total\n"
    }

    EXIT_CODE = failed ? 1 : 0
}

function report_print() {
    printf "%s", OUT_TEXT
    if (ERR_TEXT != "") {
        printf "%s", ERR_TEXT > "/dev/stderr"
        fflush("/dev/stderr")
    }
    fflush()
}

function cli_run() {
    report_build()
    report_print()
    return EXIT_CODE
}
