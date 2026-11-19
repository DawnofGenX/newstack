# Ties the pieces together without touching the filesystem or exiting.
namespace eval ::b64::runner {}

# @param argv [list] arguments without the program name
# @param io [dict] program, readFile, readStdin, write, writeErr procs
# @return [int] 0 success, 1 bad input, 2 usage
proc ::b64::runner::run {argv io} {
    set parsed [::b64::options::parse $argv]
    set status [dict get $parsed status]
    set write [dict get $io write]
    set writeErr [dict get $io writeErr]

    if {$status eq "help"} {
        $write "[::b64::options::usage [dict get $io program]]\n"
        return 0
    }
    if {$status eq "version"} {
        $write "b64 $::b64::version\n"
        return 0
    }
    if {$status eq "usage-error"} {
        $writeErr "error: [dict get $parsed message]\n[::b64::options::usage [dict get $io program]]\n"
        return 2
    }

    set options [dict get $parsed options]
    set command [dict get $parsed command]

    if {[catch {::b64::runner::input $options $io} input]} {
        $writeErr "error: $input\n"
        return 1
    }
    if {[catch {::b64::runner::apply $command $options $input} result]} {
        $writeErr "error: $result\n"
        return 1
    }

    # Raw decoded bytes are written exactly; text output gets a newline.
    if {$command eq "decode" && ![dict get $options hex]} {
        $write $result
    } else {
        $write "$result\n"
    }
    return 0
}

# @param options [dict] parsed options
# @param io [dict] reader procs
# @return [string] the raw input
proc ::b64::runner::input {options io} {
    set text [dict get $options text]
    if {$text ne ""} {
        return $text
    }
    set file [dict get $options file]
    if {$file eq "" || $file eq "-"} {
        set reader [dict get $io readStdin]
        return [$reader]
    }
    set reader [dict get $io readFile]
    return [$reader $file]
}

# @param command [string] encode or decode
# @param options [dict] parsed options
# @param input [string] the raw input
# @return [string] what to print
proc ::b64::runner::apply {command options input} {
    if {$command eq "encode"} {
        if {[dict get $options hex]} {
            set bytes [::b64::from-hex $input]
        } else {
            set bytes [encoding convertto utf-8 $input]
        }
        return [::b64::encode $bytes $options]
    }
    set bytes [::b64::decode $input]
    if {[dict get $options hex]} {
        return [::b64::to-hex $bytes]
    }
    return $bytes
}
