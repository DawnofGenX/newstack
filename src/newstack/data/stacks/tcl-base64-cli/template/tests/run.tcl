# The whole suite: source the code, run each file's checks, exit on failures.
set here [file dirname [file normalize [info script]]]
set root [file dirname $here]

source [file join $here harness.tcl]
foreach name {base64 options runner} {
    source [file join $root lib "$name.tcl"]
}

source [file join $here base64_test.tcl]
source [file join $here options_test.tcl]
source [file join $here runner_test.tcl]

::b64::test::codec::run
::b64::test::options::run
::b64::test::runner::run

exit [::harness::report]
