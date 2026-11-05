# The route table: method, path, query and body in; a status and a JSON
# document out. Pure — no socket, no global state.

namespace eval textstat::contract {}

proc textstat::contract::json_escape {value} {
    set out ""
    set length [string length $value]
    for {set index 0} {$index < $length} {incr index} {
        set char [string index $value $index]
        switch -- $char {
            "\"" { append out "\\\"" }
            "\\" { append out "\\\\" }
            "\n" { append out "\\n" }
            "\r" { append out "\\r" }
            "\t" { append out "\\t" }
            "\b" { append out "\\b" }
            "\f" { append out "\\f" }
            default {
                if {[scan $char %c] < 0x20} {
                    append out [format "\\u%04x" [scan $char %c]]
                } else {
                    append out $char
                }
            }
        }
    }
    return $out
}

proc textstat::contract::json_quote {value} {
    return "\"[json_escape $value]\""
}

proc textstat::contract::counts_json {text} {
    set counts [textstat::counts::count_text $text]
    return [format "{\"text\":%s,\"lines\":%d,\"words\":%d,\"bytes\":%d}" \
        [json_quote $text] \
        [dict get $counts lines] [dict get $counts words] [dict get $counts bytes]]
}

proc textstat::contract::error_reply {status code {detail ""}} {
    if {$detail eq ""} {
        set body "{\"error\":[json_quote $code]}"
    } else {
        set body "{\"error\":[json_quote $code],\"detail\":[json_quote $detail]}"
    }
    return [dict create status $status body $body]
}

proc textstat::contract::percent_decode {raw} {
    set out ""
    set length [string length $raw]
    for {set index 0} {$index < $length} {incr index} {
        set char [string index $raw $index]
        if {$char eq "+"} {
            append out " "
            continue
        }
        if {$char eq "%" && $index + 2 < $length} {
            set hex [string range $raw [expr {$index + 1}] [expr {$index + 2}]]
            if {[regexp {^[0-9a-fA-F]{2}$} $hex]} {
                append out [binary format H2 $hex]
                incr index 2
                continue
            }
        }
        append out $char
    }
    return $out
}

proc textstat::contract::query_param {query name} {
    if {$query eq ""} {
        return ""
    }
    foreach pair [split $query "&"] {
        if {$pair eq ""} {
            continue
        }
        set equals [string first "=" $pair]
        if {$equals < 0} {
            set key $pair
            set value ""
        } else {
            set key [string range $pair 0 [expr {$equals - 1}]]
            set value [string range $pair [expr {$equals + 1}] end]
        }
        if {[percent_decode $key] eq $name} {
            return [percent_decode $value]
        }
    }
    return ""
}

# Returns {string VALUE}, {number RAW} or {missing} for the `text` field of a
# posted body, and {invalid} when the body is not a JSON object at all.
proc textstat::contract::body_field {body} {
    if {[catch {textstat::json::decode $body} decoded]} {
        return [list invalid]
    }
    if {[lindex $decoded 0] ne "object"} {
        return [list missing]
    }
    set document [lindex $decoded 1]
    if {![dict exists $document text]} {
        return [list missing]
    }
    set field [dict get $document text]
    if {[lindex $field 0] ne "string"} {
        return [list nonstring]
    }
    return [list string [lindex $field 1]]
}

proc textstat::contract::route {method path query body} {
    if {$method eq "GET" && $path eq "/health"} {
        return [dict create status 200 body "{\"status\":\"ok\"}"]
    }
    if {$method eq "GET" && $path eq "/stats"} {
        set text [query_param $query text]
        if {$text eq "" && ![has_query_param $query text]} {
            return [error_reply 422 missing_text]
        }
        return [dict create status 200 body [counts_json $text]]
    }
    if {$method eq "POST" && $path eq "/stats"} {
        set field [body_field $body]
        switch -- [lindex $field 0] {
            invalid { return [error_reply 422 invalid_json] }
            missing { return [error_reply 422 missing_text] }
            nonstring { return [error_reply 422 missing_text] }
        }
        return [dict create status 200 body [counts_json [lindex $field 1]]]
    }
    if {$path eq "/health" || $path eq "/stats"} {
        return [error_reply 405 method_not_allowed]
    }
    return [error_reply 404 not_found "no route for $method $path"]
}

# `?text=` is a present-but-empty value; `query_param` cannot tell that from a
# missing key, so ask the query string directly.
proc textstat::contract::has_query_param {query name} {
    foreach pair [split $query "&"] {
        if {$pair eq ""} {
            continue
        }
        set equals [string first "=" $pair]
        if {$equals < 0} {
            set key $pair
        } else {
            set key [string range $pair 0 [expr {$equals - 1}]]
        }
        if {[percent_decode $key] eq $name} {
            return 1
        }
    }
    return 0
}
