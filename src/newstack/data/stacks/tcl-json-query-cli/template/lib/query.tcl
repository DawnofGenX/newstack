namespace eval ::jsonquery {}

proc ::jsonquery::query {doc path} {
    set cur $doc
    # normalize brackets to dots
    set p [string map {"[" "." "]" ""} $path]
    foreach part [split $p "."] {
        if {$part eq ""} { continue }
        if {[catch {dict exists $cur $part} de]} {
            # not a dict; try list
            set cur [lindex $cur $part]
        } elseif {$de} {
            set cur [dict get $cur $part]
        } else {
            catch { set cur [lindex $cur $part] }
        }
    }
    return $cur
}

# stack marker: tcl-json-query-cli