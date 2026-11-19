namespace eval ::json {}

proc ::json::skipws {s var} {
    upvar $var i
    set len [string length $s]
    while {$i < $len} {
        set c [string index $s $i]
        if {$c eq " " || $c eq "\t" || $c eq "\n" || $c eq "\r"} {
            incr i
        } else {
            break
        }
    }
}

proc ::json::parse_string {s var} {
    upvar $var i
    # assumes current char is quote
    incr i
    set out ""
    set len [string length $s]
    while {$i < $len} {
        set c [string index $s $i]
        if {$c eq "\\"} {
            incr i
            set esc [string index $s $i]
            switch -- $esc {
                "n" { append out "\n" }
                "t" { append out "\t" }
                "r" { append out "\r" }
                "\"" { append out "\"" }
                "\\" { append out "\\" }
                "/" { append out "/" }
                "u" {
                    set hex [string range $s [expr {$i+1}] [expr {$i+4}]]
                    append out [format %c 0x$hex]
                    incr i 4
                }
                default { append out $esc }
            }
            incr i
        } elseif {$c eq "\""} {
            incr i
            return $out
        } else {
            append out $c
            incr i
        }
    }
    error "unterminated string"
}

proc ::json::parse_number {s var} {
    upvar $var i
    set start $i
    set len [string length $s]
    while {$i < $len} {
        set c [string index $s $i]
        if {[string match {[-0-9.eE+]} $c]} {
            incr i
        } else {
            break
        }
    }
    return [string range $s $start [expr {$i - 1}]]
}

proc ::json::parse_value {s var} {
    upvar $var i
    skipws $s i
    set c [string index $s $i]
    set OB [format %c 123]
    if {$c eq $OB} { return [::json::parse_object $s i] }
    set OBR [format %c 91]
    if {$c eq $OBR} { return [::json::parse_array $s i] }
    if {$c eq "\""} { return [::json::parse_string $s i] }
    if {$c eq "t"} {
        set sub [string range $s $i [expr {$i+3}]]
        if {$sub eq "true"} {
            incr i 4
            return 1
        }
    }
    if {$c eq "f"} {
        set sub [string range $s $i [expr {$i+4}]]
        if {$sub eq "false"} {
            incr i 5
            return 0
        }
    }
    if {$c eq "n"} {
        set sub [string range $s $i [expr {$i+3}]]
        if {$sub eq "null"} {
            incr i 4
            return ""
        }
    }
    return [::json::parse_number $s i]
}

proc ::json::parse_object {s var} {
    upvar $var i
    incr i
    set obj [dict create]
    skipws $s i
    set CB [format %c 125]
    if {[string index $s $i] eq $CB} {
        incr i
        return $obj
    }
    while {1} {
        skipws $s i
        set key [::json::parse_string $s i]
        skipws $s i
        if {[string index $s $i] ne ":"} { error "expected :" }
        incr i
        set val [::json::parse_value $s i]
        dict set obj $key $val
        skipws $s i
        set c [string index $s $i]
        if {$c eq ","} {
            incr i
            continue
        }
        if {$c eq $CB} {
            incr i
            break
        }
        error "expected comma or close brace"
    }
    return $obj
}

proc ::json::parse_array {s var} {
    upvar $var i
    incr i
    set arr {}
    skipws $s i
    set CBR [format %c 93]
    if {[string index $s $i] eq $CBR} {
        incr i
        return $arr
    }
    while {1} {
        lappend arr [::json::parse_value $s i]
        skipws $s i
        set c [string index $s $i]
        if {$c eq ","} {
            incr i
            continue
        }
        if {$c eq $CBR} {
            incr i
            break
        }
        error "expected , or ]"
    }
    return $arr
}

proc ::json::parse {s} {
    set i 0
    set v [::json::parse_value $s i]
    return $v
}

# serializer
proc ::json::to_json {v} {
    if {[string is integer -strict $v] || [string is double -strict $v]} {
        # could be number or string; ambiguous; treat as value if not dict/list
        if {[llength $v] == 1} { return $v }
    }
    if {[llength $v] > 1} {
        # list
        set parts {}
        foreach item $v { lappend parts [::json::to_json $item] }
        return "\[[join $parts ,]\]"
    }
    # dict? check even? Use catch dict size
    if {![catch {dict size $v}]} {
        set parts {}
        dict for {k val} $v {
            lappend parts "\"$k\":[::json::to_json $val]"
        }
        return "[format %c 123][join $parts ,][format %c 125]"
    }
    return "\"$v\""
}