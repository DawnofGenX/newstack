# A four-line test harness: no framework, no dependencies.
namespace eval ::harness {}

set ::harness::passed 0
set ::harness::failed 0

proc ::harness::check {name actual expected} {
    if {$actual eq $expected} {
        incr ::harness::passed
        return
    }
    incr ::harness::failed
    puts "FAIL $name: got [list $actual] want [list $expected]"
}

# @return [int] the number of failures, which becomes the exit status
proc ::harness::report {} {
    set total [expr {$::harness::passed + $::harness::failed}]
    puts "$::harness::passed passed, $::harness::failed failed, $total checks"
    return $::harness::failed
}
