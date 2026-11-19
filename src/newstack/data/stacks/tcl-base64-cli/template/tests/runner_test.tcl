namespace eval ::b64::test::runner {}

set ::b64::test::runner::fakeStdin ""
set ::b64::test::runner::out ""
set ::b64::test::runner::err ""

proc ::b64::test::runner::write {text} {
    append ::b64::test::runner::out $text
}

proc ::b64::test::runner::write-err {text} {
    append ::b64::test::runner::err $text
}

proc ::b64::test::runner::read-stdin {} {
    return $::b64::test::runner::fakeStdin
}

proc ::b64::test::runner::read-file {path} {
    if {$path eq "missing.txt"} {
        error "cannot read missing.txt: no such file or directory"
    }
    return $::b64::test::runner::fakeStdin
}

# @param argv [list] CLI arguments
# @param stdin [string] what a real stdin would hold
# @return [list] output, error text, exit status
proc ::b64::test::runner::call {argv {stdin ""}} {
    set ::b64::test::runner::fakeStdin $stdin
    set ::b64::test::runner::out ""
    set ::b64::test::runner::err ""
    set io [dict create \
        program b64 \
        readFile ::b64::test::runner::read-file \
        readStdin ::b64::test::runner::read-stdin \
        write ::b64::test::runner::write \
        writeErr ::b64::test::runner::write-err]
    set status [::b64::runner::run $argv $io]
    return [list $::b64::test::runner::out $::b64::test::runner::err $status]
}

proc ::b64::test::runner::run {} {
    set checks 0

    lassign [call {encode -t foobar}] out err status
    incr checks
    ::harness::check "encode text" $out "Zm9vYmFy\n"
    ::harness::check "encode exits 0" $status 0

    lassign [call {decode -t Zm9vYmFy}] out err status
    ::harness::check "decode text" $out "foobar"
    ::harness::check "decode exits 0" $status 0

    lassign [call {decode -t Zm9vYmFy -t Zm9v}] out err status
    ::harness::check "last --text wins" $out "foo"

    lassign [call {encode --hex -t 00ff}] out err status
    ::harness::check "hex in" $out "AP8=\n"

    lassign [call {decode --hex -t AP8=}] out err status
    ::harness::check "hex out" $out "00ff\n"

    lassign [call {encode} "hello"] out err status
    ::harness::check "stdin is the default input" $out "aGVsbG8=\n"
    ::harness::check "stdin status" $status 0

    lassign [call {decode -t {not base64!!}}] out err status
    ::harness::check "bad input exits 1" $status 1
    ::harness::check "bad input message" [string match "error: invalid base64 character*" $err] 1

    lassign [call {frobnicate}] out err status
    ::harness::check "usage error exits 2" $status 2
    ::harness::check "usage error message" [string match "*expected encode or decode*" $err] 1

    lassign [call {encode --help}] out err status
    ::harness::check "help exits 0" $status 0
    ::harness::check "help text" [string match "usage: b64 encode|decode*" $out] 1

    lassign [call {encode missing.txt}] out err status
    ::harness::check "missing file exits 1" $status 1

    lassign [call {decode -t AP8=}] out err status
    ::harness::check "binary output has no newline" $out "\x00\xff"

    return $checks
}
