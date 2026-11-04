# The whole suite: source the code, run each file's checks, exit on failures.
set here [file dirname [file normalize [info script]]]
set root [file dirname $here]

source [file join $here harness.tcl]
foreach name {counts options runner} {
    source [file join $root lib "$name.tcl"]
}
source [file join $here io.tcl]

source [file join $here counts_test.tcl]
source [file join $here options_test.tcl]
source [file join $here runner_test.tcl]

::textstat::test::counts::run
::textstat::test::options::run
::textstat::test::runner::run

exit [::harness::report]
