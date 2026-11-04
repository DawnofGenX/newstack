# The whole suite: counting, parsing and reporting, all in one process. The
# only thing it does not cover is the real standard input, which the `stdin`
# verify step proves against the built wrapper.

BEGIN {
    RS = "\0"
    # The suite speaks for a fixed program so it reads the same in every
    # generated project.
    PROGRAM_NAME = "textstat"
    TMP = ".test-tmp"

    system("rm -rf " TMP " && mkdir -p " TMP)
    write_fixture(TMP "/f1.txt", "alpha beta\ngamma delta\n")
    write_fixture(TMP "/f2.txt", "alpha beta\ngamma")
    write_fixture(TMP "/empty.txt", "")
    write_fixture(TMP "/one.txt", "one\n")
    write_fixture(TMP "/a b.txt", "x y\n")

    counts_suite()
    options_suite()
    runner_suite()

    system("rm -rf " TMP)
    exit report()
}

function write_fixture(path, text) {
    printf "%s", text > path
    close(path)
}

function counts_suite(   tally) {
    counts_of("alpha beta\ngamma delta\n")
    check_int("plain: lines", COUNT_LINES, 2)
    check_int("plain: words", COUNT_WORDS, 4)
    check_int("plain: bytes", COUNT_BYTES, 23)

    counts_of("alpha beta\ngamma")
    check_int("no trailing newline: lines", COUNT_LINES, 1)
    check_int("no trailing newline: words", COUNT_WORDS, 3)
    check_int("no trailing newline: bytes", COUNT_BYTES, 16)

    counts_of("")
    check_int("empty: lines", COUNT_LINES, 0)
    check_int("empty: words", COUNT_WORDS, 0)
    check_int("empty: bytes", COUNT_BYTES, 0)

    counts_of("h" sprintf("%c", 195) sprintf("%c", 169) "llo w" sprintf("%c", 195) sprintf("%c", 182) "rld\n")
    check_int("utf8: lines", COUNT_LINES, 1)
    check_int("utf8: words", COUNT_WORDS, 2)
    check_int("utf8: bytes", COUNT_BYTES, 14)

    counts_of("a\tb\vc\fd\n")
    check_int("separators: words", COUNT_WORDS, 4)
    check_int("separators: bytes", COUNT_BYTES, 8)

    counts_of("word")
    check_int("one word, no newline: lines", COUNT_LINES, 0)
    check_int("one word, no newline: words", COUNT_WORDS, 1)

    counts_of("\n\n\n")
    check_int("blank lines: lines", COUNT_LINES, 3)
    check_int("blank lines: words", COUNT_WORDS, 0)

    counts_of("   ")
    check_int("spaces only: words", COUNT_WORDS, 0)
    check_int("spaces only: bytes", COUNT_BYTES, 3)

    check_int("figure_of lines", figure_of("lines"), 0)
    check_int("figure_of words", figure_of("words"), 0)
    check_int("figure_of bytes", figure_of("bytes"), 3)
}

function options_suite(   figures, count) {
    set_args("")
    options_parse()
    check_text("no args: status", OPT_STATUS, "ok")
    check_int("no args: no files", OPT_NFILES, 0)
    check_int("no args: all figures", OPT_SHOW_L + OPT_SHOW_W + OPT_SHOW_C, 3)

    set_args("-l")
    options_parse()
    check_int("short flag: lines only", OPT_SHOW_L + OPT_SHOW_W + OPT_SHOW_C, 1)
    check_int("short flag: show bytes", OPT_SHOW_C, 0)

    set_args("-wc")
    options_parse()
    check_int("cluster: words", OPT_SHOW_W, 1)
    check_int("cluster: bytes", OPT_SHOW_C, 1)
    check_int("cluster: no lines", OPT_SHOW_L, 0)

    set_args("--bytes")
    options_parse()
    check_int("long flag: bytes", OPT_SHOW_C, 1)

    set_args("-- --lines")
    options_parse()
    check_int("terminator: one file", OPT_NFILES, 1)
    check_text("terminator: flag is a file", OPT_FILES[1], "--lines")
    check_int("terminator: no figure flags", OPT_ANY_FIGURE, 0)

    set_args("- a.txt")
    options_parse()
    check_int("dash is a file: count", OPT_NFILES, 2)
    check_text("dash is a file: name", OPT_FILES[1], "-")

    set_args("--help")
    options_parse()
    check_text("help status", OPT_STATUS, "help")

    set_args("-V")
    options_parse()
    check_text("version status", OPT_STATUS, "version")
    check_text("version text", tool_version(), "0.1.0")

    set_args("--bogus")
    options_parse()
    check_text("unknown long: status", OPT_STATUS, "usage-error")
    check_text("unknown long: message", OPT_MESSAGE, "unknown option: --bogus")

    set_args("-x")
    options_parse()
    check_text("unknown short: message", OPT_MESSAGE, "unknown option: -x")

    set_args("-c -l")
    options_parse()
    count = options_figures(figures)
    check_int("canonical order: count", count, 2)
    check_text("canonical order: first", figures[1], "lines")
    check_text("canonical order: second", figures[2], "bytes")

    set_args("-w")
    options_parse()
    check_int("usage mentions stdin", index(usage(PROGRAM_NAME), "read standard input") > 0, 1)
}

function runner_suite(   f1, f2) {
    f1 = TMP "/f1.txt"
    f2 = TMP "/f2.txt"

    set_args(f1)
    report_build()
    check_int("one file: exit", EXIT_CODE, 0)
    check_text("one file: row", OUT_TEXT, " 2  4 23 " f1 "\n")

    set_args(f1 " " f2)
    report_build()
    check_int("two files: exit", EXIT_CODE, 0)
    check_text("two files: rows", OUT_TEXT,
               " 2  4 23 " f1 "\n 1  3 16 " f2 "\n 3  7 39 total\n")

    set_args("-l " f1)
    report_build()
    check_text("one figure, one file: no padding", OUT_TEXT, "2 " f1 "\n")

    set_args("-l -w " f1)
    report_build()
    check_text("two figures, one file: padded to bytes", OUT_TEXT, " 2  4 " f1 "\n")

    set_args("-c " f1 " " f2)
    report_build()
    check_text("bytes across two files", OUT_TEXT, "23 " f1 "\n16 " f2 "\n39 total\n")

    set_args(TMP "/one.txt")
    report_build()
    check_text("small file", OUT_TEXT, "1 1 4 " TMP "/one.txt" "\n")

    set_args(TMP "/empty.txt")
    report_build()
    check_text("empty file", OUT_TEXT, "0 0 0 " TMP "/empty.txt" "\n")

    ARGC = 2
    ARGV[1] = TMP "/a b.txt"
    report_build()
    check_int("label with a space: exit", EXIT_CODE, 0)
    check_text("label with a space: row", OUT_TEXT, "1 2 4 " TMP "/a b.txt" "\n")

    set_args(TMP "/missing.txt")
    report_build()
    check_int("missing file: exit", EXIT_CODE, 1)
    check_text("missing file: no rows", OUT_TEXT, "")
    check_text("missing file: message", ERR_TEXT, "error: cannot open '" TMP "/missing.txt'\n")

    set_args(f1 " " TMP "/missing.txt")
    report_build()
    check_int("partial failure: exit", EXIT_CODE, 1)
    check_text("partial failure: row and total", OUT_TEXT, " 2  4 23 " f1 "\n 2  4 23 total\n")

    set_args("-h")
    report_build()
    check_int("help: exit", EXIT_CODE, 0)
    check_int("help: usage first line", index(OUT_TEXT, "Usage: textstat [OPTION]... [FILE]...") == 1, 1)

    set_args("-V")
    report_build()
    check_text("version: output", OUT_TEXT, "0.1.0\n")

    set_args("--bogus")
    report_build()
    check_int("usage error: exit", EXIT_CODE, 2)
    check_text("usage error: stderr", ERR_TEXT,
               "textstat: unknown option: --bogus\nTry 'textstat --help' for more information.\n")

    set_args("--lines --bytes " f1)
    report_build()
    check_text("flag order does not leak into the row", OUT_TEXT, " 2 23 " f1 "\n")
}
