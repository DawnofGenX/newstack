# Counting that matches `wc -l -w -c`, byte for byte.
namespace eval ::textstat::counts {}

set ::textstat::counts::WHITESPACE {32 9 10 13 11 12}

# @param data [string] a byte string (open the file with "rb")
# @return [list] lines, words, bytes
proc ::textstat::counts::of-bytes {data} {
    binary scan $data cu* bytes
    set lines 0
    set words 0
    set inWord 0
    foreach byte $bytes {
        if {$byte == 10} {
            incr lines
        }
        if {$byte in $::textstat::counts::WHITESPACE} {
            set inWord 0
        } elseif {!$inWord} {
            set inWord 1
            incr words
        }
    }
    return [list $lines $words [string length $data]]
}

proc ::textstat::counts::add {left right} {
    lassign $left lines words bytes
    lassign $right dLines dWords dBytes
    return [list [expr {$lines + $dLines}] [expr {$words + $dWords}]         [expr {$bytes + $dBytes}]]
}

# @param figures [list] any of l, w, c in the order they were asked for
proc ::textstat::counts::columns {figures counts} {
    lassign $counts lines words bytes
    set out {}
    foreach figure $figures {
        switch -- $figure {
            l { lappend out $lines }
            w { lappend out $words }
            c { lappend out $bytes }
            default { error "unknown figure: $figure" }
        }
    }
    return $out
}
