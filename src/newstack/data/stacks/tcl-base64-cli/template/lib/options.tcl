# A hand-written argv parser for encode/decode.
namespace eval ::b64::options {}

# @param program [string] the name to show in the usage message
# @return [string] the usage text
proc ::b64::options::usage {program} {
    return "usage: $program encode|decode \[options\] \[FILE\]

Encode the input as base64, or decode base64 back to bytes.  With no FILE, or
when FILE is -, read standard input.

  --url          use the URL-safe alphabet (- and _) and drop padding when encoding
  --no-padding   drop the trailing = characters
  --hex          treat the input as hex (encode) or print hex (decode)
  -t, --text S   use S as the input instead of a file or stdin
  -h, --help     show this message
  -V, --version  show the version
"
}

# @param argv [list] arguments without the program name
# @return [dict] status ok|help|version|usage-error, message, command, options
proc ::b64::options::parse {argv} {
    set status ok
    set message ""
    set command ""
    set options [dict create url 0 padding 1 hex 0 text ""]
    set file ""
    set onlyFiles 0
    set index 0
    set length [llength $argv]

    while {$index < $length} {
        set arg [lindex $argv $index]
        incr index

        if {$onlyFiles} {
            if {$file ne ""} {
                return [dict create status usage-error message "only one FILE may be given" command $command options $options]
            }
            set file $arg
            continue
        }
        if {$arg eq "--"} {
            set onlyFiles 1
            continue
        }
        switch -- $arg {
            -h - --help {
                set status help
                break
            }
            -V - --version {
                set status version
                break
            }
            --url {
                dict set options url 1
            }
            --no-padding {
                dict set options padding 0
            }
            --hex {
                dict set options hex 1
            }
            -t - --text {
                if {$index >= $length} {
                    return [dict create status usage-error message "$arg needs a value" command $command options $options]
                }
                dict set options text [lindex $argv $index]
                incr index
            }
            encode - decode {
                if {$command ne ""} {
                    return [dict create status usage-error message "only one of encode and decode may be given" command $command options $options]
                }
                set command $arg
            }
            default {
                if {[string index $arg 0] eq "-" && $arg ne "-"} {
                    return [dict create status usage-error message "unknown option '$arg'" command $command options $options]
                }
                if {$file ne ""} {
                    return [dict create status usage-error message "only one FILE may be given" command $command options $options]
                }
                set file $arg
            }
        }
    }

    if {$status ne "ok"} {
        return [dict create status $status message "" command $command options $options]
    }
    if {$command eq ""} {
        return [dict create status usage-error message "expected encode or decode" command "" options $options]
    }
    dict set options file $file
    return [dict create status ok message "" command $command options $options]
}
