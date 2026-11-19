namespace eval ::b64::test::options {}

proc ::b64::test::options::run {} {
    set checks 0

    set parsed [::b64::options::parse {encode --url --no-padding --hex -t abc}]
    incr checks
    ::harness::check "status ok" [dict get $parsed status] "ok"
    ::harness::check "command" [dict get $parsed command] "encode"
    ::harness::check "url flag" [dict get [dict get $parsed options] url] 1
    ::harness::check "padding flag" [dict get [dict get $parsed options] padding] 0
    ::harness::check "hex flag" [dict get [dict get $parsed options] hex] 1
    ::harness::check "inline text" [dict get [dict get $parsed options] text] "abc"

    set parsed [::b64::options::parse {decode -t -- Zm9v}]
    ::harness::check "text may start with a dash" [dict get [dict get $parsed options] text] "--"

    set parsed [::b64::options::parse {decode -- --weird-file}]
    ::harness::check "file after --" [dict get [dict get $parsed options] file] "--weird-file"

    set cases [list]
    lappend cases [list {frobnicate} "expected encode or decode"]
    lappend cases [list {encode --bogus} "unknown option '--bogus'"]
    lappend cases [list {encode -t} "-t needs a value"]
    lappend cases [list {encode a.txt b.txt} "only one FILE may be given"]
    lappend cases [list {encode decode} "only one of encode and decode may be given"]
    foreach case $cases {
        lassign $case argv expected
        set parsed [::b64::options::parse $argv]
        incr checks
        ::harness::check "rejects '$argv'" [dict get $parsed status] "usage-error"
        ::harness::check "message for '$argv'" [dict get $parsed message] $expected
    }

    set cases [list]
    lappend cases [list {--help} help]
    lappend cases [list {encode -h} help]
    lappend cases [list {--version} version]
    lappend cases [list {decode -V} version]
    foreach case $cases {
        lassign $case argv status
        incr checks
        ::harness::check "'$argv'" [dict get [::b64::options::parse $argv] status] $status
    }

    return $checks
}
