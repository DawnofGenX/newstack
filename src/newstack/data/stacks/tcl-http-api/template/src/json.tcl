# A small JSON reader: enough for an object of scalars, and strict enough that a
# body which is not JSON is reported as such instead of half-parsed.
#
# Objects come back as a dict whose values are two-element lists: {string V},
# {number RAW} or {literal RAW}. Keeping numbers apart from strings is the whole
# point — `{"text": 42}` must not count as text.

namespace eval textstat::json {}

proc textstat::json::fail {message} {
    return -code error -errorcode {TEXTSTAT JSON} $message
}

proc textstat::json::skip_ws {stateName} {
    upvar 1 $stateName state
    set text [dict get $state text]
    set index [dict get $state index]
    while {$index < [string length $text]} {
        set char [string index $text $index]
        if {$char ne " " && $char ne "\t" && $char ne "\n" && $char ne "\r"} {
            break
        }
        incr index
    }
    dict set state index $index
}

proc textstat::json::peek {stateName} {
    upvar 1 $stateName state
    set text [dict get $state text]
    set index [dict get $state index]
    if {$index >= [string length $text]} {
        return ""
    }
    return [string index $text $index]
}

proc textstat::json::expect {stateName wanted} {
    upvar 1 $stateName state
    skip_ws state
    if {[peek state] ne $wanted} {
        fail "expected '$wanted' at [dict get $state index]"
    }
    dict incr state index
}

proc textstat::json::parse_string {stateName} {
    upvar 1 $stateName state
    set text [dict get $state text]
    expect state "\x22"
    set index [dict get $state index]
    set out ""
    while {$index < [string length $text]} {
        set char [string index $text $index]
        if {$char eq "\""} {
            dict set state index [expr {$index + 1}]
            return $out
        }
        if {$char eq "\\"} {
            incr index
            if {$index >= [string length $text]} {
                fail "unterminated escape"
            }
            set escape [string index $text $index]
            switch -- $escape {
                "\"" { append out "\"" }
                "\\" { append out "\\" }
                "/"  { append out "/" }
                "b"  { append out "\b" }
                "f"  { append out "\f" }
                "n"  { append out "\n" }
                "r"  { append out "\r" }
                "t"  { append out "\t" }
                "u"  {
                    set hex [string range $text [expr {$index + 1}] [expr {$index + 4}]]
                    if {![regexp {^[0-9a-fA-F]{4}$} $hex]} {
                        fail "bad \\u escape"
                    }
                    append out [format %c [scan $hex %x]]
                    incr index 4
                }
                default { fail "unknown escape \\$escape" }
            }
            incr index
            continue
        }
        if {[scan $char %c] < 0x20} {
            fail "control character in string"
        }
        append out $char
        incr index
    }
    fail "unterminated string"
}

proc textstat::json::parse_number {stateName} {
    upvar 1 $stateName state
    set text [dict get $state text]
    set index [dict get $state index]
    # `-start` does not move the start anchor with `^` in Tcl, so match without
    # the caret: the caller has already checked that a digit or '-' sits here.
    if {![regexp -start $index {(-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][-+]?[0-9]+)?)} $text raw]} {
        fail "bad number at $index"
    }
    dict set state index [expr {$index + [string length $raw]}]
    return [list number $raw]
}

proc textstat::json::parse_value {stateName} {
    upvar 1 $stateName state
    skip_ws state
    set char [peek state]
    if {$char eq "\x22"} {
        return [list string [parse_string state]]
    }
    if {$char eq "\x7b"} {
        return [list object [parse_object state]]
    }
    if {$char eq "\x5b"} {
        fail "arrays are not part of this contract"
    }
    if {$char eq ""} {
        fail "unexpected end of input"
    }
    foreach literal {true false null} {
        if {[string equal -length [string length $literal] $literal \
                [string range [dict get $state text] [dict get $state index] end]]} {
            dict incr state index [string length $literal]
            return [list literal $literal]
        }
    }
    return [parse_number state]
}

proc textstat::json::parse_object {stateName} {
    upvar 1 $stateName state
    expect state "\x7b"
    set result [dict create]
    skip_ws state
    if {[peek state] eq "\x7d"} {
        dict incr state index
        return $result
    }
    while {1} {
        set key [parse_string state]
        expect state ":"
        set value [parse_value state]
        dict set result $key $value
        skip_ws state
        set char [peek state]
        if {$char eq ","} {
            dict incr state index
            continue
        }
        if {$char eq "\x7d"} {
            dict incr state index
            return $result
        }
        fail "expected ',' or '\}' at [dict get $state index]"
    }
}

# Returns the parsed document, or throws.
proc textstat::json::decode {text} {
    set state [dict create text $text index 0]
    set value [parse_value state]
    skip_ws state
    if {[dict get $state index] < [string length $text]} {
        fail "trailing data at [dict get $state index]"
    }
    return $value
}
