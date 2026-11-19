# The only file that touches the real process: files, stdin, stdout and exit.
set here [file dirname [file normalize [info script]]]
foreach name {base64 options runner} {
    source [file join $here lib "$name.tcl"]
}

namespace eval ::b64::main {}

proc ::b64::main::read-file {path} {
    set channel [open $path rb]
    try {
        return [read $channel]
    } finally {
        close $channel
    }
}

proc ::b64::main::read-stdin {} {
    fconfigure stdin -translation binary
    return [read stdin]
}

proc ::b64::main::write {text} {
    chan puts -nonewline stdout $text
}

proc ::b64::main::write-err {text} {
    chan puts -nonewline stderr $text
}

fconfigure stdout -translation binary

set io [dict create \
    program [file tail [file normalize [info script]]] \
    readFile ::b64::main::read-file \
    readStdin ::b64::main::read-stdin \
    write ::b64::main::write \
    writeErr ::b64::main::write-err]
exit [::b64::runner::run $argv $io]
