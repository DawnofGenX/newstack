namespace eval ::textstat::test::counts {}

proc ::textstat::test::counts::bytes {values} {
    return [binary format cu* $values]
}

proc ::textstat::test::counts::run {} {
    ::harness::check "empty" [::textstat::counts::of-bytes ""] {0 0 0}
    ::harness::check "one line" [::textstat::counts::of-bytes "alpha beta\ngamma\n"] {2 3 17}
    ::harness::check "no trailing newline" \
        [::textstat::counts::of-bytes "one line, no trailing newline"] {0 5 29}
    ::harness::check "utf-8 is counted in bytes" \
        [::textstat::counts::of-bytes [::textstat::test::counts::bytes \
            {104 195 169 108 108 111 32 119 195 182 114 108 100 10}]] {1 2 14}
    ::harness::check "tab, vertical tab and form feed separate words" \
        [::textstat::counts::of-bytes "a\tb\vc\fd\n"] {1 4 8}
    ::harness::check "carriage return is whitespace but not a line" \
        [::textstat::counts::of-bytes "a\r\nb"] {1 2 4}
    ::harness::check "add" [::textstat::counts::add {1 2 3} {4 5 6}] {5 7 9}
    ::harness::check "columns in asked order" \
        [::textstat::counts::columns {c l} {7 8 9}] {9 7}
}
