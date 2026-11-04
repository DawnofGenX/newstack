# A four-function harness: check, check_int, check_text, report. Nothing here
# knows what is being tested; the suite drives report_build() in-process.

function reset_run(   i) {
    PASSED = 0
    FAILED = 0
    OUT_TEXT = ""
    ERR_TEXT = ""
    EXIT_CODE = 0
    OPT_NFILES = 0
    for (i in OPT_FILES) {
        delete OPT_FILES[i]
    }
    for (i in ROW_LABEL) {
        delete ROW_LABEL[i]
    }
    for (i in ROW_LINES) {
        delete ROW_LINES[i]
    }
    for (i in ROW_WORDS) {
        delete ROW_WORDS[i]
    }
    for (i in ROW_BYTES) {
        delete ROW_BYTES[i]
    }
}

function check(name, ok,   detail) {
    if (ok) {
        PASSED++
        return
    }
    FAILED++
    print "FAIL " name
}

function check_int(name, actual, expected) {
    check(name, actual == expected, "got [" actual "] want [" expected "]")
}

function check_text(name, actual, expected) {
    if (actual == expected) {
        PASSED++
        return
    }
    FAILED++
    printf "FAIL %s: got [%s] want [%s]\n", name, actual, expected
}

# Sets ARGV/ARGC from a space-separated argument line so options_parse() sees
# exactly what a shell would have passed.
function set_args(line,   parts, i, n) {
    n = split(line, parts, " ")
    ARGC = 1
    for (i = 1; i <= n; i++) {
        if (parts[i] != "") {
            ARGV[ARGC++] = parts[i]
        }
    }
}

function report() {
    printf "checks: %d, passed: %d, failed: %d\n", PASSED + FAILED, PASSED, FAILED
    return FAILED
}
