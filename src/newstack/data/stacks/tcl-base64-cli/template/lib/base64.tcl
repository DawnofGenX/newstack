# RFC 4648 base64 and base64url, written against plain byte strings.
namespace eval ::b64 {}

set ::b64::version 0.1.0

set ::b64::standard "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
set ::b64::urlSafe "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

proc ::b64::build-maps {} {
    set ::b64::encodeMap [dict create]
    set ::b64::decodeMap [dict create]
    for {set index 0} {$index < 64} {incr index} {
        set standard [string index $::b64::standard $index]
        set url [string index $::b64::urlSafe $index]
        set bits [format %06b $index]
        dict set ::b64::encodeMap $index $standard
        dict set ::b64::decodeMap $standard [list $index $bits]
        if {$url ne $standard} {
            dict set ::b64::decodeMap $url [list $index $bits]
        }
    }
}

::b64::build-maps

# @param bytes [binary] the payload
# @param options [dict] url (0|1) and padding (0|1)
# @return [string] the encoded text
proc ::b64::encode {bytes {options {}}} {
    set url [expr {[dict exists $options url] ? [dict get $options url] : 0}]
    set padding [expr {[dict exists $options padding] ? [dict get $options padding] : 1}]
    if {$url} {
        set table $::b64::urlSafe
    } else {
        set table $::b64::standard
    }

    set bits ""
    binary scan $bytes B* bits
    set length [string length $bits]
    if {$length % 6} {
        append bits [string repeat 0 [expr {6 - ($length % 6)}]]
    }

    set out ""
    set sextets [expr {[string length $bits] / 6}]
    for {set index 0} {$index < $sextets} {incr index} {
        set sextet [string range $bits [expr {$index * 6}] [expr {$index * 6 + 5}]]
        append out [string index $table [scan $sextet %b]]
    }

    if {$padding} {
        set remainder [expr {[string length $bytes] % 3}]
        if {$remainder == 1} {
            append out "=="
        } elseif {$remainder == 2} {
            append out "="
        }
    }
    return $out
}

# @param text [string] base64 or base64url, whitespace and padding tolerated
# @return [binary] the decoded payload
proc ::b64::decode {text} {
    regsub -all {\s} $text "" text
    if {[regexp {=.*[^=]} $text]} {
        error "invalid padding: '=' may only appear at the end"
    }
    set text [string trimright $text "="]
    if {$text eq ""} {
        return ""
    }
    if {[regexp -indices {[^A-Za-z0-9+/_-]} $text match]} {
        lassign $match start end
        error "invalid base64 character '[string index $text $start]' at position [expr {$start + 1}]"
    }
    set remainder [expr {[string length $text] % 4}]
    if {$remainder == 1} {
        error "truncated base64: [string length $text] characters cannot encode whole bytes"
    }

    set bits ""
    set position 0
    foreach char [split $text ""] {
        incr position
        if {![dict exists $::b64::decodeMap $char]} {
            error "invalid base64 character '$char' at position $position"
        }
        lassign [dict get $::b64::decodeMap $char] index sextet
        append bits $sextet
    }

    set leftover [expr {[string length $bits] % 8}]
    if {$leftover ni {0 2 4}} {
        error "unexpected padding: base64 text encoded half a byte"
    }
    if {$leftover} {
        if {[string trim [string range $bits end-[expr {$leftover - 1}] end] 0] ne ""} {
            error "non-zero padding bits: base64 text was truncated"
        }
        set bits [string range $bits 0 end-$leftover]
    }

    set out ""
    set count [expr {[string length $bits] / 8}]
    for {set index 0} {$index < $count} {incr index} {
        append out [format %c [scan [string range $bits [expr {$index * 8}] [expr {$index * 8 + 7}]] %b]]
    }
    return $out
}

# @param bytes [binary] the payload
# @return [string] lowercase hex, two characters per byte
proc ::b64::to-hex {bytes} {
    binary scan $bytes H* hex
    return $hex
}

# @param text [string] hex digits, even length
# @return [binary] the payload
proc ::b64::from-hex {text} {
    if {[string length $text] % 2} {
        error "hex input needs an even number of digits, got [string length $text]"
    }
    if {![regexp {^[0-9a-fA-F]*$} $text]} {
        error "hex input contains a non-hex character"
    }
    if {$text eq ""} {
        return ""
    }
    return [binary format H* $text]
}
