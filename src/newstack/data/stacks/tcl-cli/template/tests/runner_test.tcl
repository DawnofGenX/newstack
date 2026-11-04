namespace eval ::textstat::test::runner {}

proc ::textstat::test::runner::run {} {
    lassign [::textstat::test::run {-w} "alpha beta\ngamma\n" {}] code out err
    ::harness::check "stdin gets the stdin label" $out "3 -"
    ::harness::check "a good run exits zero" $code 0

    lassign [::textstat::test::run {} "alpha beta\ngamma\n" {}] code out err
    ::harness::check "no flags prints every figure" $out " 2  3 17 -"

    lassign [::textstat::test::run {a.txt b.txt} "" \
        [dict create a.txt "alpha beta\ngamma\n" b.txt "x\n"]] code out err
    ::harness::check "two files share one width" $out " 2  3 17 a.txt\n 1  1  2 b.txt\n 3  4 19 total"
    ::harness::check "two files exit zero" $code 0

    lassign [::textstat::test::run {a.txt missing.txt} "" \
        [dict create a.txt "alpha beta\ngamma\n"]] code out err
    ::harness::check "an unreadable file is reported once" $err "error: cannot open 'missing.txt'"
    ::harness::check "an unreadable file exits one" $code 1
    ::harness::check "the readable file is still printed" [lindex [split $out "\n"] 0] " 2  3 17 a.txt"
    ::harness::check "so is the total" [lindex [split $out "\n"] end] " 2  3 17 total"

    lassign [::textstat::test::run {--bogus} "" {}] code out err
    ::harness::check "a usage error exits two" $code 2
    ::harness::check "the first line names the option" [lindex [split $err "\n"] 0] \
        "${::textstat::runner::program}: unknown option: --bogus"
    ::harness::check "the second line points at the help" [lindex [split $err "\n"] 1] \
        "Try '${::textstat::runner::program} --help' for more information."

    lassign [::textstat::test::run {--help} "" {}] code out err
    ::harness::check "help exits zero" $code 0
    ::harness::check "help starts with its usage line" [lindex [split $out "\n"] 0] \
        "usage: ${::textstat::runner::program} \[-l\] \[-w\] \[-c\] \[FILE ...\]"

    lassign [::textstat::test::run {--version} "" {}] code out err
    ::harness::check "version prints the version" $out "${::textstat::runner::program} 0.1.0"
    ::harness::check "version exits zero" $code 0
}
