namespace eval ::textstat::test::options {}

proc ::textstat::test::options::field {argv key} {
    return [dict get [::textstat::options::parse $argv] $key]
}

proc ::textstat::test::options::run {} {
    ::harness::check "no arguments asks for every figure" \
        [::textstat::test::options::field {} figures] {l w c}
    ::harness::check "no arguments means stdin" \
        [::textstat::test::options::field {} files] {}
    ::harness::check "one flag" [::textstat::test::options::field {-l} figures] {l}
    ::harness::check "a cluster" [::textstat::test::options::field {-lw} figures] {l w}
    ::harness::check "a repeated flag is not repeated" \
        [::textstat::test::options::field {-ll} figures] {l}
    ::harness::check "the long form" [::textstat::test::options::field {--bytes} figures] {c}
    ::harness::check "flag then file" \
        [::textstat::test::options::field {-c notes.txt} files] {notes.txt}
    ::harness::check "dash means stdin" [::textstat::test::options::field {-} files] {-}
    ::harness::check "-- ends the options" \
        [::textstat::test::options::field {-- -l} files] {-l}
    ::harness::check "help" [::textstat::test::options::field {--help} status] help
    ::harness::check "short help" [::textstat::test::options::field {-h} status] help
    ::harness::check "version" [::textstat::test::options::field {--version} status] version
    ::harness::check "unknown long option" \
        [::textstat::test::options::field {--bogus} message] "unknown option: --bogus"
    ::harness::check "unknown short option" \
        [::textstat::test::options::field {-x} message] "unknown option: -x"
    ::harness::check "unknown option is a usage error" \
        [::textstat::test::options::field {-x} status] usage-error
    ::harness::check "a cluster with a bad letter" \
        [::textstat::test::options::field {-lx} status] usage-error
}
