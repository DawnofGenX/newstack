# The only file that touches the real process: the filesystem, stdin, and exit.
set here [file dirname [file normalize [info script]]]
foreach name {counts options runner} {
    source [file join $here lib "$name.tcl"]
}

namespace eval ::textstat::main {}

proc ::textstat::main::read-file {path} {
    set channel [open $path rb]
    try {
        return [read $channel]
    } finally {
        close $channel
    }
}

proc ::textstat::main::read-stdin {} {
    fconfigure stdin -translation binary
    return [read stdin]
}

set io [dict create \
    readFile ::textstat::main::read-file \
    readStdin ::textstat::main::read-stdin \
    out stdout \
    err stderr]
exit [::textstat::runner::run $argv $io]
