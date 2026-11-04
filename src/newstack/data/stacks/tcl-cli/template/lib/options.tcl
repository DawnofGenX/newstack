# A hand-written argv parser: the one option set this tool has.
namespace eval ::textstat::options {}

set ::textstat::options::version 0.1.0

proc ::textstat::options::usage {program} {
    return "usage: $program \[-l\] \[-w\] \[-c\] \[FILE ...\]

Count lines, words and bytes.  Each figure is printed only when its flag is
given; with no flags all three are.  With no FILE, or when FILE is -, read
standard input.

  -l, --lines    lines
  -w, --words    words
  -c, --bytes    bytes
  -h, --help     show this message
  -V, --version  show the version
"
}

# @param argv [list] the command-line arguments, without the program name
# @return [dict] status ok|help|version|usage-error, message, figures, files
proc ::textstat::options::parse {argv} {
    set figures {}
    set files {}
    set status ok
    set message ""
    set onlyFiles 0
    set index 0
    set length [llength $argv]

    while {$index < $length} {
        set arg [lindex $argv $index]
        incr index

        if {$onlyFiles} {
            lappend files $arg
            continue
        }
        if {$arg eq "--"} {
            set onlyFiles 1
            continue
        }
        if {$arg eq "-h" || $arg eq "--help"} {
            set status help
            break
        }
        if {$arg eq "-V" || $arg eq "--version"} {
            set status version
            break
        }
        if {$arg eq "-"} {
            lappend files $arg
            continue
        }
        if {[string match "--*" $arg]} {
            set aliases {lines l words w bytes c help h version V}
            set name [string range $arg 2 end]
            if {![dict exists $aliases $name]} {
                set status usage-error
                set message "unknown option: $arg"
                break
            }
            set arg "-[dict get $aliases $name]"
        }
        if {[string length $arg] > 1 && [string index $arg 0] eq "-"} {
            foreach letter [split [string range $arg 1 end] ""] {
                if {$letter ni {l w c}} {
                    set status usage-error
                    set message "unknown option: -$letter"
                    break
                }
                if {$letter ni $figures} {
                    lappend figures $letter
                }
            }
            if {$status ne "ok"} {
                break
            }
            continue
        }
        lappend files $arg
    }

    if {$status eq "ok" && [llength $figures] == 0} {
        set figures {l w c}
    }
    return [dict create status $status message $message figures $figures files $files]
}
