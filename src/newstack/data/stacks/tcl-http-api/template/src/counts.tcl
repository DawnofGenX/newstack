# Counting over the bytes Tcl already holds: a request body and a decoded query
# value are byte strings, so `string length` is the byte count.

namespace eval textstat::counts {}

proc textstat::counts::count_text {text} {
    set lines 0
    set words 0
    set in_word 0
    set length [string length $text]
    for {set index 0} {$index < $length} {incr index} {
        set char [string index $text $index]
        if {$char eq "\n"} {
            incr lines
        }
        if {$char eq " " || $char eq "\t" || $char eq "\n" || $char eq "\r"
                || $char eq "\v" || $char eq "\f"} {
            set in_word 0
        } elseif {!$in_word} {
            set in_word 1
            incr words
        }
    }
    return [dict create lines $lines words $words bytes $length]
}
