# The process-facing layer: it decides what to print and which code to exit.
namespace eval ::textstat::runner {}

set ::textstat::runner::program "{{ npm_name }}"

proc ::textstat::runner::format-row {values label width} {
    set cells {}
    foreach value $values {
        lappend cells [format %*d $width $value]
    }
    return "[join $cells " "] $label"
}

# @param argv [list] command-line arguments without the program name
# @param io [dict] readFile (path -> bytes), readStdin, out, err channels
# @return [int] 0 ok, 1 a file could not be read, 2 usage error
proc ::textstat::runner::run {argv io} {
    set parsed [::textstat::options::parse $argv]
    set status [dict get $parsed status]
    set out [dict get $io out]
    set err [dict get $io err]

    switch -- $status {
        help {
            puts $out [::textstat::options::usage $::textstat::runner::program]
            return 0
        }
        version {
            puts $out "$::textstat::runner::program $::textstat::options::version"
            return 0
        }
        usage-error {
            puts $err "$::textstat::runner::program: [dict get $parsed message]"
            puts $err "Try '$::textstat::runner::program --help' for more information."
            return 2
        }
    }

    set figures [dict get $parsed figures]
    set files [dict get $parsed files]
    if {[llength $files] == 0} {
        set files [list "-"]
    }

    set rows {}
    set total {0 0 0}
    set failed 0
    set readFile [dict get $io readFile]
    set readStdin [dict get $io readStdin]
    foreach path $files {
        if {$path eq "-"} {
            set data [$readStdin]
        } elseif {[catch {$readFile $path} data]} {
            puts $err "error: cannot open '$path'"
            set failed 1
            continue
        }
        set counts [::textstat::counts::of-bytes $data]
        set total [::textstat::counts::add $total $counts]
        lappend rows [list $path $counts]
    }

    set printed $rows
    if {[llength $files] > 1} {
        lappend printed [list total $total]
    }

    set width 1
    foreach row $printed {
        foreach value [::textstat::counts::columns $figures [lindex $row 1]] {
            set width [expr {max($width, [string length [format %d $value]])}]
        }
    }
    foreach row $printed {
        set values [::textstat::counts::columns $figures [lindex $row 1]]
        puts $out [::textstat::runner::format-row $values [lindex $row 0] $width]
    }
    return $failed
}
